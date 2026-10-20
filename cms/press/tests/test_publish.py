import datetime
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from press import publish as publish_mod
from press.export import export_published
from press.publish import (PUBLISH_BRANCH, GhPullRequests, GitError, PublishResult, PullRequestError,
                           SubprocessGit, publish)
from press.tests.test_models import make_article

FIXED_NOW = datetime.datetime(2026, 10, 20, 9, 5)
OLD = '{"old": true}\n'
PR_URL = "https://github.com/o/r/pull/7"


def files(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


class FakeGit:
    """Simulates origin/main as the directory `base`; the worktree is a copy of it."""

    def __init__(self, base: Path, *, matches=False, push_error=None, fetch_error=None):
        self.base, self.matches, self.push_error, self.fetch_error = base, matches, push_error, fetch_error
        self.commits, self.pushes, self.worktrees, self.removed = [], 0, [], []

    def fetch(self):
        if self.fetch_error:
            raise GitError(self.fetch_error)

    def add_worktree(self, path):
        shutil.copytree(self.base, path)
        self.worktrees.append(path)

    def remove_worktree(self, path):
        self.removed.append(path)
        shutil.rmtree(path, ignore_errors=True)

    def has_changes(self, worktree, paths):
        pick = lambda root: {k: v for k, v in files(root).items() if k.startswith(tuple(paths))}
        return pick(worktree) != pick(self.base)

    def commit(self, worktree, paths, message):
        self.commits.append((list(paths), message))

    def matches_publish_branch(self, worktree):
        return self.matches

    def push_publish_branch(self, worktree):
        self.pushes += 1
        if self.push_error:
            raise GitError(self.push_error)

    def compare_url(self):
        return "https://github.com/o/r/compare/main...news/publish?expand=1"


class FakePRs:
    def __init__(self, open_url=None, error=None):
        self.open_url, self.error, self.created, self.closed = open_url, error, [], []

    def find_open(self):
        if self.error:
            raise PullRequestError(self.error)
        return self.open_url

    def create(self, title, body):
        self.created.append((title, body))
        return PR_URL

    def close(self, url, comment):
        self.closed.append(url)
        self.open_url = None


class PublishTests(TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)
        # origin/main as seen by FakeGit
        self.base = root / "origin-main"
        (self.base / "content").mkdir(parents=True)
        (self.base / "static/img/news").mkdir(parents=True)
        (self.base / "content/news.json").write_text(OLD, encoding="utf-8")
        (self.base / "static/img/news/.gitkeep").write_text("")
        # the owner's own checkout, which publishing must never touch
        self.repo = root / "repo"
        shutil.copytree(self.base, self.repo)
        (self.repo / "content/draft-notes.txt").write_text("uncommitted work")
        self.before = files(self.repo)
        ov = override_settings(MEDIA_ROOT=root / "media")
        ov.enable()
        self.addCleanup(ov.disable)
        make_article(slug="pub-1", status="published").save()

    def run_publish(self, git=None, prs=None, tests=lambda r: (True, "ok")):
        self.git = git or FakeGit(self.base)
        self.prs = prs or FakePRs()
        return publish(self.repo, git=self.git, prs=self.prs, run_tests=tests, now=lambda: FIXED_NOW)

    def tearDown(self):
        # whatever happened, the owner's checkout is unchanged and the worktree is gone
        self.assertEqual(files(self.repo), self.before)
        for wt in getattr(self, "git", FakeGit(self.base)).worktrees:
            self.assertIn(wt, self.git.removed)
            self.assertFalse(wt.exists())

    def test_creates_pull_request(self):
        r = self.run_publish()
        self.assertEqual(r.status, "pr_created")
        self.assertEqual(r.url, PR_URL)
        self.assertIn("GitHub で内容を確認してマージ", r.message)
        self.assertEqual(self.git.commits, [(["content", "static/img/news"], "news: サイトに反映 (2026-10-20 09:05)")])
        self.assertEqual(self.git.pushes, 1)
        self.assertEqual(len(self.prs.created), 1)

    def test_tests_run_in_the_worktree_on_the_export(self):
        seen = []

        def tests(root):
            seen.append((root, (root / "content/news.json").read_text(encoding="utf-8")))
            return True, "ok"
        self.run_publish(tests=tests)
        self.assertEqual(seen[0][0], self.git.worktrees[0])
        self.assertIn('"pub-1"', seen[0][1])

    def test_updates_open_pull_request(self):
        r = self.run_publish(prs=FakePRs(open_url=PR_URL))
        self.assertEqual(r.status, "pr_updated")
        self.assertEqual(r.url, PR_URL)
        self.assertEqual(self.git.pushes, 1)
        self.assertEqual(self.prs.created, [])

    def test_pending_branch_already_current(self):
        r = self.run_publish(git=FakeGit(self.base, matches=True), prs=FakePRs(open_url=PR_URL))
        self.assertEqual(r.status, "no_changes")
        self.assertEqual(r.url, PR_URL)
        self.assertEqual(self.git.pushes, 0)

    def test_pending_branch_current_but_pr_closed_reopens_one(self):
        r = self.run_publish(git=FakeGit(self.base, matches=True))
        self.assertEqual(r.status, "pr_created")
        self.assertEqual(self.git.pushes, 0)
        self.assertEqual(len(self.prs.created), 1)

    def test_no_changes_against_main(self):
        export_published(self.base)  # main already holds exactly this export
        r = self.run_publish()
        self.assertEqual(r.status, "no_changes")
        self.assertEqual((self.git.commits, self.git.pushes), ([], 0))

    def test_reverting_to_main_closes_the_pending_pr(self):
        # e.g. an article published (PR opened) and then set back to draft before merging:
        # the open PR would publish it, so it must not survive
        export_published(self.base)
        r = self.run_publish(prs=FakePRs(open_url=PR_URL))
        self.assertEqual(r.status, "pr_closed")
        self.assertEqual(self.prs.closed, [PR_URL])
        self.assertIn("マージ不要", r.message)
        self.assertEqual((self.git.commits, self.git.pushes), ([], 0))

    def test_reverting_to_main_warns_when_pending_pr_cannot_be_checked(self):
        export_published(self.base)
        r = self.run_publish(prs=FakePRs(error="gh コマンドが見つかりません"))
        self.assertEqual(r.status, "pr_failed")
        self.assertIn("マージせずに閉じてください", r.message)

    def test_tests_failed(self):
        r = self.run_publish(tests=lambda root: (False, "boom"))
        self.assertEqual(r.status, "tests_failed")
        self.assertIn("boom", r.output)
        self.assertEqual((self.git.commits, self.git.pushes), ([], 0))

    def test_export_error_blocks(self):
        a = make_article(slug="gone-1", title="画像欠落", status="published",
                         image=SimpleUploadedFile("g.png", b"d"), image_alt="a")
        a.save()
        Path(a.image.path).unlink()
        r = self.run_publish()
        self.assertEqual(r.status, "blocked")
        self.assertIn("gone-1", r.message)
        self.assertEqual(self.git.commits, [])

    def test_fetch_failure_blocks_before_anything(self):
        r = self.run_publish(git=FakeGit(self.base, fetch_error="offline"))
        self.assertEqual(r.status, "blocked")
        self.assertIn("offline", r.message)
        self.assertEqual(self.git.worktrees, [])

    def test_push_failure(self):
        r = self.run_publish(git=FakeGit(self.base, push_error="Could not resolve host"))
        self.assertEqual(r.status, "push_failed")
        self.assertIn("GitHub への送信に失敗しました", r.message)
        self.assertEqual(self.prs.created, [])

    def test_push_refused_because_branch_changed_elsewhere(self):
        r = self.run_publish(git=FakeGit(self.base, push_error="! [rejected] (stale info)"))
        self.assertEqual(r.status, "push_failed")
        self.assertIn("もう一度「サイトに反映」を押してください", r.message)

    def test_pr_failure_offers_manual_link(self):
        r = self.run_publish(prs=FakePRs(error="gh コマンドが見つかりません"))
        self.assertEqual(r.status, "pr_failed")
        self.assertIn("gh コマンドが見つかりません", r.message)
        self.assertEqual(r.url, "https://github.com/o/r/compare/main...news/publish?expand=1")

    def test_unexpected_error_blocks_and_cleans_up(self):
        with mock.patch("press.publish.export_published", side_effect=OSError("disk full")):
            r = self.run_publish()
        self.assertEqual(r.status, "blocked")
        self.assertIn("予期しないエラーが発生しました: disk full", r.message)

    def test_concurrent_publish_is_blocked(self):
        self.assertTrue(publish_mod._publish_lock.acquire(blocking=False))
        try:
            r = self.run_publish()
        finally:
            publish_mod._publish_lock.release()
        self.assertEqual(r.status, "blocked")
        self.assertIn("別の反映処理が実行中です", r.message)
        self.assertEqual(self.git.worktrees, [])
        self.assertEqual(self.run_publish().status, "pr_created")  # lock released afterwards

    def test_run_site_tests_timeout_is_failure(self):
        with mock.patch("press.publish.subprocess.run", side_effect=subprocess.TimeoutExpired("x", 300)):
            ok, out = publish_mod.run_site_tests(self.repo)
        self.assertFalse(ok)
        self.assertIn("タイムアウト", out)


def sh(*args, cwd):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout


class SubprocessGitTests(TestCase):
    """Real git against a throwaway bare repo standing in for GitHub."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.remote = self.root / "remote.git"
        self.repo = self.root / "work"
        sh("git", "init", "--bare", "-b", "main", str(self.remote), cwd=self.root)
        self.repo.mkdir()
        self.init_clone(self.repo)
        (self.repo / "content").mkdir()
        (self.repo / "content/news.json").write_text("[]\n")
        (self.repo / "static/img/news").mkdir(parents=True)
        (self.repo / "static/img/news/.gitkeep").write_text("")
        (self.repo / "other.txt").write_text("x")
        sh("git", "add", "-A", cwd=self.repo)
        sh("git", "commit", "-m", "init", cwd=self.repo)
        sh("git", "push", "origin", "main", cwd=self.repo)
        (self.repo / "other.txt").write_text("owner's uncommitted edit")

    def init_clone(self, path):
        sh("git", "init", "-b", "main", cwd=path)
        for k, v in (("user.name", "t"), ("user.email", "t@example.com"), ("commit.gpgsign", "false")):
            sh("git", "config", k, v, cwd=path)
        sh("git", "remote", "add", "origin", str(self.remote), cwd=path)

    def publish_once(self, news: str) -> SubprocessGit:
        git = SubprocessGit(self.repo)
        git.fetch()
        wt = self.root / f"wt-{news.strip()}"
        git.add_worktree(wt)
        try:
            (wt / "content/news.json").write_text(news)
            if git.has_changes(wt, publish_mod.COMMIT_PATHS):
                git.commit(wt, publish_mod.COMMIT_PATHS, f"news: {news.strip()}")
            if not git.matches_publish_branch(wt):
                git.push_publish_branch(wt)
        finally:
            git.remove_worktree(wt)
        return git

    def remote_log(self, ref):
        return sh("git", "log", "--format=%s", ref, cwd=self.remote).split("\n")[0]

    def test_pushes_publish_branch_and_leaves_owner_checkout_alone(self):
        self.publish_once("[1]\n")
        self.assertEqual(self.remote_log(PUBLISH_BRANCH), "news: [1]")
        self.assertEqual(self.remote_log("main"), "init")
        self.assertEqual(sh("git", "rev-parse", "--abbrev-ref", "HEAD", cwd=self.repo).strip(), "main")
        self.assertEqual(sh("git", "log", "--format=%s", cwd=self.repo).split(), ["init"])
        self.assertEqual((self.repo / "other.txt").read_text(), "owner's uncommitted edit")
        self.assertEqual(len(sh("git", "worktree", "list", cwd=self.repo).splitlines()), 1)

    def test_republish_replaces_branch_on_top_of_new_main(self):
        self.publish_once("[1]\n")
        other = self.root / "other-clone"
        other.mkdir()
        self.init_clone(other)
        sh("git", "pull", "origin", "main", cwd=other)
        (other / "README").write_text("new on main")
        sh("git", "add", "README", cwd=other)
        sh("git", "commit", "-m", "main moved", cwd=other)
        sh("git", "push", "origin", "main", cwd=other)
        self.publish_once("[2]\n")
        log = sh("git", "log", "--format=%s", PUBLISH_BRANCH, cwd=self.remote).split("\n")
        self.assertEqual(log[:3], ["news: [2]", "main moved", "init"])  # one commit on top of main

    def test_identical_export_does_not_push_again(self):
        self.publish_once("[1]\n")
        sha = sh("git", "rev-parse", PUBLISH_BRANCH, cwd=self.remote)
        self.publish_once("[1]\n")
        self.assertEqual(sh("git", "rev-parse", PUBLISH_BRANCH, cwd=self.remote), sha)

    def test_push_refused_when_branch_changed_after_fetch(self):
        self.publish_once("[1]\n")
        git = SubprocessGit(self.repo)
        git.fetch()
        wt = self.root / "wt-race"
        git.add_worktree(wt)
        self.addCleanup(git.remove_worktree, wt)
        (wt / "content/news.json").write_text("[race]\n")
        git.commit(wt, publish_mod.COMMIT_PATHS, "news: race")
        self.publish_once("[someone else]\n")  # the branch moves on GitHub meanwhile
        with self.assertRaises(GitError) as cm:
            git.push_publish_branch(wt)
        self.assertIn("stale info", str(cm.exception))

    def test_fetch_failure_raises(self):
        sh("git", "remote", "set-url", "origin", str(self.remote) + "-missing", cwd=self.repo)
        with self.assertRaises(GitError):
            SubprocessGit(self.repo).fetch()

    def test_compare_url(self):
        git = SubprocessGit(self.repo)
        for remote in ("https://github.com/o/r.git", "git@github.com:o/r.git", "https://github.com/o/r"):
            sh("git", "remote", "set-url", "origin", remote, cwd=self.repo)
            self.assertEqual(git.compare_url(), "https://github.com/o/r/compare/main...news/publish?expand=1")
        sh("git", "remote", "set-url", "origin", str(self.remote), cwd=self.repo)
        self.assertIsNone(git.compare_url())

    def test_end_to_end_publish(self):
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=Path(media)):
            make_article(slug="pub-1", status="published").save()
            prs = FakePRs()
            r = publish(self.repo, prs=prs, run_tests=lambda root: (True, "ok"), now=lambda: FIXED_NOW)
        self.assertEqual(r.status, "pr_created", r.message)
        self.assertEqual(self.remote_log(PUBLISH_BRANCH), "news: サイトに反映 (2026-10-20 09:05)")
        news = sh("git", "show", f"{PUBLISH_BRANCH}:content/news.json", cwd=self.remote)
        self.assertIn('"pub-1"', news)
        self.assertEqual((self.repo / "content/news.json").read_text(), "[]\n")
        self.assertEqual(len(sh("git", "worktree", "list", cwd=self.repo).splitlines()), 1)


class GhPullRequestsTests(TestCase):
    def run_gh(self, stdout="", returncode=0, stderr=""):
        done = subprocess.CompletedProcess([], returncode, stdout=stdout, stderr=stderr)
        return mock.patch("press.publish.subprocess.run", return_value=done)

    def test_find_open(self):
        with self.run_gh(PR_URL + "\n") as run:
            self.assertEqual(GhPullRequests(Path(".")).find_open(), PR_URL)
        self.assertIn("--head", run.call_args.args[0])
        with self.run_gh(""):
            self.assertIsNone(GhPullRequests(Path(".")).find_open())

    def test_close_deletes_branch(self):
        with self.run_gh() as run:
            GhPullRequests(Path(".")).close(PR_URL, "c")
        args = run.call_args.args[0]
        self.assertEqual(args[:4], ["gh", "pr", "close", PR_URL])
        self.assertIn("--delete-branch", args)

    def test_create_returns_url(self):
        with self.run_gh("Creating pull request...\n" + PR_URL + "\n"):
            self.assertEqual(GhPullRequests(Path(".")).create("t", "b"), PR_URL)

    def test_errors(self):
        with self.run_gh(returncode=1, stderr="not logged in"), self.assertRaises(PullRequestError) as cm:
            GhPullRequests(Path(".")).find_open()
        self.assertIn("not logged in", str(cm.exception))
        with mock.patch("press.publish.subprocess.run", side_effect=FileNotFoundError):
            with self.assertRaises(PullRequestError) as cm:
                GhPullRequests(Path(".")).create("t", "b")
        self.assertIn("gh コマンドが見つかりません", str(cm.exception))


class PublishAdminTests(TestCase):
    def login(self):
        self.client.force_login(get_user_model().objects.create_superuser("admin", "a@example.com", "pw"))

    def test_admin_publish_requires_post_and_staff(self):
        url = reverse("admin:press_article_publish")
        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("admin:login"), r["Location"])
        self.login()
        with mock.patch("press.views.publish") as p:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200)
            self.assertContains(r, "PR（変更の提案）を作成します")
            p.assert_not_called()

    def test_changelist_has_button(self):
        self.login()
        r = self.client.get(reverse("admin:press_article_changelist"))
        self.assertContains(r, reverse("admin:press_article_publish"))
        self.assertContains(r, "サイトに反映")

    def test_admin_publish_shows_pr_link(self):
        self.login()
        res = PublishResult("pr_created", "PR を作成しました。", PR_URL)
        with mock.patch("press.views.publish", return_value=res):
            r = self.client.post(reverse("admin:press_article_publish"), follow=True)
        self.assertRedirects(r, reverse("admin:press_article_changelist"))
        self.assertContains(r, f'PR を作成しました。 <a href="{PR_URL}" target="_blank" rel="noopener">{PR_URL}</a>',
                            html=False)
        self.assertEqual([m.level_tag for m in get_messages(r.wsgi_request)], ["success"])

    def test_admin_publish_failure_levels_and_pre(self):
        self.login()
        res = PublishResult("tests_failed", "テストが失敗したため反映を中止しました", output="<b>trace</b>")
        with mock.patch("press.views.publish", return_value=res):
            r = self.client.post(reverse("admin:press_article_publish"))
        msgs = list(get_messages(r.wsgi_request))
        self.assertEqual(msgs[0].level_tag, "error")
        self.assertIn("&lt;b&gt;trace&lt;/b&gt;", str(msgs[0]))
        self.assertIn("<pre>", str(msgs[0]))
