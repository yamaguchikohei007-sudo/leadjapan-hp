import datetime
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
from press.publish import GitError, PublishResult, SubprocessGit, publish
from press.tests.test_models import make_article

FIXED_NOW = datetime.datetime(2026, 10, 20, 9, 5)
OLD = '{"old": true}\n'


class FakeGit:
    def __init__(self, branch="main", changes=True, push_error=None):
        self.branch, self.changes, self.push_error = branch, changes, push_error
        self.commits, self.pushes, self.change_checks = [], 0, 0
        self.ahead = 0

    def unpushed_commits(self):
        return self.ahead

    def current_branch(self):
        return self.branch

    def has_changes(self, paths):
        self.change_checks += 1
        return self.changes

    def commit(self, paths, message):
        self.commits.append((list(paths), message))
        self.ahead += 1

    def push(self):
        self.pushes += 1
        if self.push_error:
            raise GitError(self.push_error)
        self.ahead = 0


class PublishTests(TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)
        self.repo = root / "repo"
        (self.repo / "content").mkdir(parents=True)
        (self.repo / "static/img/news").mkdir(parents=True)
        (self.repo / "content/news.json").write_text(OLD, encoding="utf-8")
        (self.repo / "static/img/news/old.png").write_bytes(b"old")
        ov = override_settings(MEDIA_ROOT=root / "media")
        ov.enable()
        self.addCleanup(ov.disable)
        make_article(slug="pub-1", status="published").save()

    def run_publish(self, git, tests=lambda r: (True, "ok")):
        return publish(self.repo, git=git, run_tests=tests, now=lambda: FIXED_NOW)

    def assert_restored(self):
        self.assertEqual((self.repo / "content/news.json").read_text(encoding="utf-8"), OLD)
        self.assertEqual((self.repo / "static/img/news/old.png").read_bytes(), b"old")
        self.assertEqual([p.name for p in (self.repo / "static/img/news").iterdir()], ["old.png"])

    def test_tests_failed_restores_files_and_skips_git(self):
        git = FakeGit()
        r = self.run_publish(git, lambda root: (False, "boom"))
        self.assertEqual(r.status, "tests_failed")
        self.assertIn("boom", r.output)
        self.assertEqual(git.commits, [])
        self.assert_restored()

    def test_tests_failed_restores_when_news_json_did_not_exist(self):
        (self.repo / "content/news.json").unlink()
        r = self.run_publish(FakeGit(), lambda root: (False, "boom"))
        self.assertEqual(r.status, "tests_failed")
        self.assertFalse((self.repo / "content/news.json").exists())

    def test_no_changes(self):
        git = FakeGit(changes=False)
        r = self.run_publish(git)
        self.assertEqual(r.status, "no_changes")
        self.assertEqual(git.commits, [])

    def test_published_commits_only_content_paths(self):
        git = FakeGit()
        r = self.run_publish(git)
        self.assertEqual(r.status, "published")
        self.assertEqual(len(git.commits), 1)
        paths, message = git.commits[0]
        self.assertEqual(paths, ["content", "static/img/news"])
        self.assertEqual(message, "news: サイトに反映 (2026-10-20 09:05)")
        self.assertEqual(git.pushes, 1)
        self.assertEqual(r.url, "https://yamaguchikohei007-sudo.github.io/leadjapan-hp/")
        self.assertIn("数分でサイトに反映されます", r.message)

    def test_push_failure_reports_and_keeps_commit(self):
        git = FakeGit(push_error="offline")
        r = self.run_publish(git)
        self.assertEqual(r.status, "push_failed")
        self.assertIn("offline", r.message)
        self.assertEqual(len(git.commits), 1)
        self.assertNotEqual((self.repo / "content/news.json").read_text(encoding="utf-8"), OLD)

    def test_push_rejected_remote_has_newer_commits(self):
        for err in ("! [rejected] main -> main (fetch first)", "non-fast-forward", "updates were rejected"):
            git = FakeGit(push_error=err)
            r = self.run_publish(git)
            self.assertEqual(r.status, "push_failed")
            self.assertIn("GitHub 側に新しい変更があるため送信できませんでした。サイトの管理者に連絡してください。",
                          r.message)
            self.assertIn(err, r.message)

    def test_concurrent_publish_is_blocked(self):
        self.assertTrue(publish_mod._publish_lock.acquire(blocking=False))
        try:
            git = FakeGit()
            r = self.run_publish(git)
        finally:
            publish_mod._publish_lock.release()
        self.assertEqual(r.status, "blocked")
        self.assertIn("別の反映処理が実行中です。しばらく待ってから再度お試しください。", r.message)
        self.assertEqual(git.commits, [])
        self.assertEqual(self.run_publish(FakeGit()).status, "published")  # lock released afterwards

    def test_unexpected_error_restores_and_blocks(self):
        git = FakeGit()
        with mock.patch("press.publish.export_published", side_effect=OSError("disk full")):
            r = self.run_publish(git)
        self.assertEqual(r.status, "blocked")
        self.assertIn("予期しないエラーが発生しました: disk full", r.message)
        self.assertEqual(git.commits, [])
        self.assert_restored()
        self.assertEqual(self.run_publish(FakeGit()).status, "published")

    def test_unexpected_error_after_export_restores(self):
        def boom(root):
            raise OSError("tests crashed")
        r = self.run_publish(FakeGit(), boom)
        self.assertEqual(r.status, "blocked")
        self.assertIn("tests crashed", r.message)
        self.assert_restored()

    def test_no_changes_but_unpushed_commit_gets_pushed(self):
        git = FakeGit(push_error="offline")
        self.assertEqual(self.run_publish(git).status, "push_failed")
        git.push_error = None
        git.changes = False
        r = self.run_publish(git)
        self.assertEqual(r.status, "published")
        self.assertEqual(git.pushes, 2)
        self.assertEqual(len(git.commits), 1)

    def test_no_changes_and_nothing_unpushed_does_not_push(self):
        git = FakeGit(changes=False)
        self.assertEqual(self.run_publish(git).status, "no_changes")
        self.assertEqual(git.pushes, 0)

    def test_export_keeps_gitkeep(self):
        (self.repo / "static/img/news/.gitkeep").write_text("")
        self.run_publish(FakeGit())
        self.assertTrue((self.repo / "static/img/news/.gitkeep").exists())

    def test_run_site_tests_timeout_is_failure(self):
        with mock.patch("press.publish.subprocess.run",
                        side_effect=subprocess.TimeoutExpired("x", 300)):
            ok, out = publish_mod.run_site_tests(self.repo)
        self.assertFalse(ok)
        self.assertIn("タイムアウト", out)

    def test_blocked_on_other_branch_does_nothing(self):
        git = FakeGit(branch="feature/x")
        r = self.run_publish(git)
        self.assertEqual(r.status, "blocked")
        self.assertIn("main ブランチで実行してください（現在: feature/x）", r.message)
        self.assertEqual(git.commits, [])
        self.assertEqual(git.change_checks, 0)
        self.assert_restored()

    def test_export_error_blocks_and_restores(self):
        a = make_article(slug="gone-1", title="画像欠落", status="published", image=SimpleUploadedFile("g.png", b"d"),
                         image_alt="a")
        a.save()
        Path(a.image.path).unlink()
        git = FakeGit()
        r = self.run_publish(git)
        self.assertEqual(r.status, "blocked")
        self.assertIn("gone-1", r.message)
        self.assertEqual(git.commits, [])
        self.assert_restored()


def sh(*args, cwd):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout


class SubprocessGitTests(TestCase):
    """Runs only against a throwaway repo with a local bare remote."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)
        self.remote = root / "remote.git"
        self.repo = root / "work"
        self.repo.mkdir()
        sh("git", "init", "--bare", "-b", "main", str(self.remote), cwd=root)
        sh("git", "init", "-b", "main", cwd=self.repo)
        for k, v in (("user.name", "t"), ("user.email", "t@example.com"), ("commit.gpgsign", "false")):
            sh("git", "config", k, v, cwd=self.repo)
        sh("git", "remote", "add", "origin", str(self.remote), cwd=self.repo)
        (self.repo / "content").mkdir()
        (self.repo / "content/news.json").write_text("[]\n")
        (self.repo / "other.txt").write_text("x")
        sh("git", "add", "-A", cwd=self.repo)
        sh("git", "commit", "-m", "init", cwd=self.repo)
        self.git = SubprocessGit(self.repo)

    def test_branch_changes_commit_and_push(self):
        self.assertEqual(self.git.current_branch(), "main")
        self.assertFalse(self.git.has_changes(["content"]))
        (self.repo / "content/news.json").write_text("[1]\n")
        (self.repo / "other.txt").write_text("changed")
        self.assertTrue(self.git.has_changes(["content"]))
        self.git.commit(["content"], "news: test")
        self.assertEqual(sh("git", "log", "-1", "--format=%s", cwd=self.repo).strip(), "news: test")
        self.assertIn("other.txt", sh("git", "status", "--porcelain", cwd=self.repo))
        self.git.push()
        self.assertEqual(sh("git", "log", "-1", "--format=%s", "main", cwd=self.remote).strip(), "news: test")

    def test_commit_text_only_when_image_dir_missing_or_empty(self):
        for make_empty in (False, True):
            with self.subTest(empty_dir=make_empty):
                img = self.repo / "static/img/news"
                if make_empty:
                    img.mkdir(parents=True, exist_ok=True)
                (self.repo / "content/news.json").write_text(f"[{make_empty}]\n")
                self.assertTrue(self.git.has_changes(publish_mod.COMMIT_PATHS))
                self.git.commit(publish_mod.COMMIT_PATHS, "news: text only")
                self.assertEqual(sh("git", "log", "-1", "--format=%s", cwd=self.repo).strip(), "news: text only")
                self.assertFalse(self.git.has_changes(publish_mod.COMMIT_PATHS))

    def test_commit_leaves_unrelated_staged_file_alone(self):
        (self.repo / "content/news.json").write_text("[2]\n")
        (self.repo / "other.txt").write_text("staged change")
        sh("git", "add", "other.txt", cwd=self.repo)
        self.git.commit(publish_mod.COMMIT_PATHS, "news: only content")
        self.assertEqual(sh("git", "show", "--name-only", "--format=", "HEAD", cwd=self.repo).split(),
                         ["content/news.json"])
        self.assertIn("M  other.txt", sh("git", "status", "--porcelain", cwd=self.repo))

    def test_failed_commit_unstages_paths(self):
        (self.repo / "content/news.json").write_text("[3]\n")
        sh("git", "config", "core.hooksPath", str(self.repo / "hooks"), cwd=self.repo)
        (self.repo / "hooks").mkdir()
        hook = self.repo / "hooks/pre-commit"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        with self.assertRaises(GitError):
            self.git.commit(publish_mod.COMMIT_PATHS, "news: nope")
        self.assertNotIn("M  content/news.json", sh("git", "status", "--porcelain", cwd=self.repo))

    def test_unpushed_commits_counts_ahead_of_origin(self):
        self.git.push()
        self.assertEqual(self.git.unpushed_commits(), 0)
        (self.repo / "content/news.json").write_text("[4]\n")
        self.git.commit(publish_mod.COMMIT_PATHS, "news: ahead")
        self.assertEqual(self.git.unpushed_commits(), 1)

    def test_push_failure_raises_git_error(self):
        sh("git", "remote", "set-url", "origin", str(self.remote) + "-missing", cwd=self.repo)
        with self.assertRaises(GitError):
            self.git.push()


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
            self.assertContains(r, "サイトに反映")
            p.assert_not_called()

    def test_changelist_has_button(self):
        self.login()
        r = self.client.get(reverse("admin:press_article_changelist"))
        self.assertContains(r, reverse("admin:press_article_publish"))
        self.assertContains(r, "サイトに反映")

    def test_admin_publish_shows_message(self):
        self.login()
        res = PublishResult("published", "数分でサイトに反映されます: https://example.com/", "https://example.com/")
        with mock.patch("press.views.publish", return_value=res):
            r = self.client.post(reverse("admin:press_article_publish"), follow=True)
        self.assertRedirects(r, reverse("admin:press_article_changelist"))
        self.assertContains(r, "数分でサイトに反映されます: https://example.com/")

    def test_admin_publish_failure_levels_and_pre(self):
        self.login()
        res = PublishResult("tests_failed", "テストが失敗したため反映を中止しました", output="<b>trace</b>")
        with mock.patch("press.views.publish", return_value=res):
            r = self.client.post(reverse("admin:press_article_publish"))
        msgs = list(get_messages(r.wsgi_request))
        self.assertEqual(msgs[0].level_tag, "error")
        self.assertIn("&lt;b&gt;trace&lt;/b&gt;", str(msgs[0]))
        self.assertIn("<pre>", str(msgs[0]))
