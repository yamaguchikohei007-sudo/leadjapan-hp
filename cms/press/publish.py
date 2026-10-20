"""「サイトに反映」: export published articles and open (or update) a pull request.

Everything happens in a temporary git worktree checked out from the latest
origin/main, so the owner's own checkout (its branch, uncommitted files) is never
touched and nothing needs restoring after a failure. The site goes live only when
the owner merges the pull request on GitHub.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Literal, Protocol

from django.utils import timezone

from .export import IMAGE_DIR, ExportError, export_published

BASE_BRANCH = "main"
PUBLISH_BRANCH = "news/publish"  # one pending pull request at a time, refreshed on every publish
COMMIT_PATHS = ["content", IMAGE_DIR]
PR_TITLE = "news: サイトに反映"
PR_BODY = ("管理画面の「サイトに反映」で作成しました（サイトのテストは成功済み）。\n\n"
           "内容を確認してマージすると、数分で公開サイトに反映されます。")
_publish_lock = threading.Lock()


class GitError(Exception):
    pass


class PullRequestError(Exception):
    pass


@dataclass
class PublishResult:
    status: Literal["pr_created", "pr_updated", "pr_closed", "no_changes", "tests_failed", "push_failed",
                    "pr_failed", "blocked"]
    message: str
    url: str | None = None
    output: str = ""


class Git(Protocol):
    def fetch(self) -> None: ...
    def add_worktree(self, path: Path) -> None: ...
    def remove_worktree(self, path: Path) -> None: ...
    def has_changes(self, worktree: Path, paths: list[str]) -> bool: ...
    def commit(self, worktree: Path, paths: list[str], message: str) -> None: ...
    def matches_publish_branch(self, worktree: Path) -> bool: ...
    def push_publish_branch(self, worktree: Path) -> None: ...
    def compare_url(self) -> str | None: ...


class PullRequests(Protocol):
    def find_open(self) -> str | None: ...
    def create(self, title: str, body: str) -> str: ...
    def close(self, url: str, comment: str) -> None: ...


class SubprocessGit:
    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
        self._publish_sha: str | None = None  # origin's news/publish at fetch time ("" = absent)

    def _run(self, *args: str, cwd: Path | None = None, timeout: int = 120) -> str:
        env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        try:
            p = subprocess.run(["git", *args], cwd=cwd or self.repo_root, capture_output=True, text=True,
                               timeout=timeout, env=env)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise GitError(f"git {args[0]}: {e}") from e
        if p.returncode != 0:
            raise GitError((p.stderr or p.stdout).strip() or f"git {args[0]} failed ({p.returncode})")
        return p.stdout

    def fetch(self) -> None:
        self._run("fetch", "--prune", "origin", BASE_BRANCH)
        out = self._run("ls-remote", "--heads", "origin", PUBLISH_BRANCH).split()
        self._publish_sha = out[0] if out else ""
        if self._publish_sha:
            self._run("fetch", "origin", f"+{PUBLISH_BRANCH}:refs/remotes/origin/{PUBLISH_BRANCH}")

    def add_worktree(self, path: Path) -> None:
        self._run("worktree", "add", "--detach", str(path), f"origin/{BASE_BRANCH}")

    def remove_worktree(self, path: Path) -> None:
        try:
            self._run("worktree", "remove", "--force", str(path))
        finally:
            self._run("worktree", "prune")

    @staticmethod
    def _usable(worktree: Path, paths: list[str]) -> list[str]:
        """Drop pathspecs git would reject: neither tracked nor holding any file on disk."""
        keep = []
        for p in paths:
            full = worktree / p
            if full.is_file() or (full.is_dir() and any(f.is_file() for f in full.rglob("*"))):
                keep.append(p)
        return keep

    def has_changes(self, worktree: Path, paths: list[str]) -> bool:
        paths = self._usable(worktree, paths)
        if not paths:
            return False
        out = self._run("status", "--porcelain", "--untracked-files=all", "--", *paths, cwd=worktree)
        return bool(out.strip())

    def commit(self, worktree: Path, paths: list[str], message: str) -> None:
        paths = self._usable(worktree, paths)
        if not paths:
            raise GitError("コミット対象のファイルがありません")
        self._run("add", "-A", "--", *paths, cwd=worktree)
        self._run("commit", "-m", message, cwd=worktree)

    def matches_publish_branch(self, worktree: Path) -> bool:
        """True when the pending branch already holds exactly this tree (nothing to push)."""
        if not self._publish_sha:
            return False
        ours = self._run("rev-parse", "HEAD^{tree}", cwd=worktree).strip()
        theirs = self._run("rev-parse", f"{self._publish_sha}^{{tree}}", cwd=worktree).strip()
        return ours == theirs

    def push_publish_branch(self, worktree: Path) -> None:
        # The branch only ever holds the latest export on top of main, so it is
        # replaced; the lease refuses if someone changed it since our fetch.
        lease = f"--force-with-lease={PUBLISH_BRANCH}:{self._publish_sha or ''}"
        self._run("push", lease, "origin", f"HEAD:refs/heads/{PUBLISH_BRANCH}", cwd=worktree)

    def compare_url(self) -> str | None:
        """GitHub page for opening the pull request by hand (when gh is unavailable)."""
        try:
            remote = self._run("remote", "get-url", "origin").strip()
        except GitError:
            return None
        m = re.search(r"github\.com[:/]([^/]+)/(.+?)(?:\.git)?/?$", remote)
        if not m:
            return None
        return f"https://github.com/{m[1]}/{m[2]}/compare/{BASE_BRANCH}...{PUBLISH_BRANCH}?expand=1"


class GhPullRequests:
    """Pull requests through the GitHub CLI (`gh`), logged in on this Mac."""

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)

    def _run(self, *args: str) -> str:
        try:
            p = subprocess.run(["gh", *args], cwd=self.repo_root, capture_output=True, text=True, timeout=60)
        except FileNotFoundError as e:
            raise PullRequestError("gh コマンドが見つかりません（GitHub CLI をインストールしてください）") from e
        except (OSError, subprocess.TimeoutExpired) as e:
            raise PullRequestError(f"gh {args[0]}: {e}") from e
        if p.returncode != 0:
            raise PullRequestError((p.stderr or p.stdout).strip() or f"gh {args[0]} failed ({p.returncode})")
        return p.stdout

    def find_open(self) -> str | None:
        out = self._run("pr", "list", "--head", PUBLISH_BRANCH, "--base", BASE_BRANCH, "--state", "open",
                        "--json", "url", "--jq", ".[0].url // empty")
        return out.strip() or None

    def create(self, title: str, body: str) -> str:
        out = self._run("pr", "create", "--base", BASE_BRANCH, "--head", PUBLISH_BRANCH,
                        "--title", title, "--body", body)
        urls = re.findall(r"https://\S+", out)
        if not urls:
            raise PullRequestError(f"PR の URL を読み取れません: {out.strip()}")
        return urls[-1]

    def close(self, url: str, comment: str) -> None:
        self._run("pr", "close", url, "--delete-branch", "--comment", comment)


def run_site_tests(repo_root: Path) -> tuple[bool, str]:
    try:
        p = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                           cwd=repo_root, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return False, "テストがタイムアウトしました（300秒）"
    out = "\n".join(((p.stdout or "") + (p.stderr or "")).splitlines()[-40:])
    return p.returncode == 0, out


def _publish(repo_root: Path, *, git: Git | None = None, prs: PullRequests | None = None,
             run_tests: Callable[[Path], tuple[bool, str]] = run_site_tests,
             now: Callable[[], datetime] = timezone.localtime) -> PublishResult:
    repo_root = Path(repo_root)
    git = git or SubprocessGit(repo_root)
    prs = prs or GhPullRequests(repo_root)

    try:
        git.fetch()
    except GitError as e:
        return PublishResult("blocked", f"GitHub から最新の状態を取得できません（オフラインやログイン切れなど）: {e}")

    tmp = Path(tempfile.mkdtemp(prefix="leadjapan-publish-"))
    worktree = tmp / "site"
    try:
        try:
            git.add_worktree(worktree)
        except GitError as e:
            return PublishResult("blocked", f"作業用のコピーを作れません: {e}")
        try:
            return _publish_in(worktree, git, prs, run_tests, now)
        finally:
            try:
                git.remove_worktree(worktree)
            except GitError:
                pass  # the temp dir is removed below; `git worktree prune` tidies up later
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _publish_in(worktree: Path, git: Git, prs: PullRequests,
                run_tests: Callable[[Path], tuple[bool, str]], now: Callable[[], datetime]) -> PublishResult:
    try:
        export_published(worktree)
    except ExportError as e:
        return PublishResult("blocked", str(e))
    ok, output = run_tests(worktree)
    if not ok:
        return PublishResult("tests_failed", "テストが失敗したため反映を中止しました", output=output)

    if not git.has_changes(worktree, COMMIT_PATHS):
        return _withdraw_pending(prs)
    try:
        git.commit(worktree, COMMIT_PATHS, f"news: サイトに反映 ({now():%Y-%m-%d %H:%M})")
    except GitError as e:
        return PublishResult("blocked", f"コミットに失敗しました: {e}")

    pushed = False
    if not git.matches_publish_branch(worktree):
        try:
            git.push_publish_branch(worktree)
        except GitError as e:
            if any(s in str(e).lower() for s in ("stale info", "rejected", "fetch first")):
                return PublishResult("push_failed", "反映待ちの PR が別の場所で更新されていたため送信しませんでした。"
                                                    f"もう一度「サイトに反映」を押してください。（{e}）")
            return PublishResult("push_failed", f"GitHub への送信に失敗しました（オフラインやログイン切れなど）: {e}")
        pushed = True

    try:
        url = prs.find_open()
        if url:
            if not pushed:
                return PublishResult("no_changes", "反映待ちの PR はすでに最新です。GitHub でマージしてください。", url)
            return PublishResult("pr_updated", "反映待ちの PR を最新の内容に更新しました。GitHub で確認してマージしてください。",
                                 url)
        url = prs.create(PR_TITLE, PR_BODY)
    except PullRequestError as e:
        manual = git.compare_url()
        return PublishResult("pr_failed", f"送信はできましたが、PR を作成できませんでした: {e}。"
                                          "次のリンクから PR を作成してください。", manual)
    return PublishResult("pr_created", "PR を作成しました。GitHub で内容を確認してマージすると、数分でサイトに反映されます。",
                         url)


def _withdraw_pending(prs: PullRequests) -> PublishResult:
    """The export equals main. A still-open pending PR now holds content the
    owner has taken back (e.g. an article returned to draft): merging it would
    publish that, so it is closed and its branch deleted."""
    try:
        url = prs.find_open()
        if url:
            prs.close(url, "管理画面の内容が公開中のサイトと同じに戻ったため、この PR は不要になりました"
                           "（管理画面の「サイトに反映」が自動で閉じました）。")
    except PullRequestError as e:
        return PublishResult("pr_failed", f"公開中のサイトと同じ内容ですが、反映待ちの PR が残っていないか確認できませんでした: {e}。"
                                          "GitHub に開いたままの「news: サイトに反映」の PR があれば、マージせずに閉じてください。")
    if url:
        return PublishResult("pr_closed", "公開中のサイトと同じ内容に戻ったため、反映待ちの PR を閉じました（マージ不要です）。", url)
    return PublishResult("no_changes", "変更はありません（公開中のサイトと同じ内容です）")


def publish(repo_root: Path, **kwargs) -> PublishResult:
    """Run one publish at a time; a second concurrent call is refused, not queued."""
    if not _publish_lock.acquire(blocking=False):
        return PublishResult("blocked", "別の反映処理が実行中です。しばらく待ってから再度お試しください。")
    try:
        return _publish(repo_root, **kwargs)
    except Exception as e:  # unexpected (OSError etc.): never surface as a 500
        return PublishResult("blocked", f"予期しないエラーが発生しました: {e}")
    finally:
        _publish_lock.release()
