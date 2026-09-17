from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src")}


def run(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        env=ENV,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )
    if check and completed.returncode != 0:
        raise AssertionError(f"{args} failed\nstdout={completed.stdout}\nstderr={completed.stderr}")
    return completed


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=repo, check=check)


def ggcp(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run([sys.executable, "-m", "granular_git_commit_push.cli", *args], cwd=repo, check=check)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class RepoFixture:
    def __init__(self, branch: str = "main", remote: bool = True) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="ggcp-pytest-"))
        self.repo = self.temp / "repo with spaces"
        self.remote = self.temp / "remote.git"
        self.branch = branch
        if remote:
            git(self.temp, "init", "--bare", str(self.remote))
        self.repo.mkdir()
        init = git(self.repo, "init", "-b", branch, check=False)
        if init.returncode != 0:
            git(self.repo, "init")
            git(self.repo, "checkout", "-b", branch)
        git(self.repo, "config", "user.name", "Test User")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "core.autocrlf", "false")
        write(self.repo / "README.md", "# Fixture\n")
        write(self.repo / "src" / "app.txt", "one\n")
        write(self.repo / "src" / "keep.txt", "keep\n")
        git(self.repo, "add", "--", "README.md", "src/app.txt", "src/keep.txt")
        git(self.repo, "commit", "-m", "chore: initial")
        if remote:
            git(self.repo, "remote", "add", "origin", str(self.remote))
            git(self.repo, "push", "-u", "origin", branch)

    def cleanup(self) -> None:
        shutil.rmtree(self.temp, ignore_errors=True)


class GgcpCliTests(unittest.TestCase):
    def fixture(self, branch: str = "main", remote: bool = True) -> RepoFixture:
        fixture = RepoFixture(branch=branch, remote=remote)
        self.addCleanup(fixture.cleanup)
        return fixture

    def test_version_and_help(self) -> None:
        self.assertIn("0.2.0", run([sys.executable, "-m", "granular_git_commit_push.cli", "--version"]).stdout)
        self.assertEqual(run([sys.executable, "-m", "granular_git_commit_push.cli", "--help"]).returncode, 0)

    def test_clean_repository(self) -> None:
        fixture = self.fixture()
        data = json.loads(ggcp(fixture.repo, "inspect", "--json").stdout)
        self.assertEqual(data["changes"], [])

    def test_doctor_json_parses(self) -> None:
        fixture = self.fixture()
        data = json.loads(ggcp(fixture.repo, "doctor", "--json").stdout)
        self.assertTrue(data["git"]["available"])
        self.assertEqual(data["repository"]["branch"], "main")

    def test_inspect_json_contains_stable_keys(self) -> None:
        fixture = self.fixture()
        data = json.loads(ggcp(fixture.repo, "inspect", "--json").stdout)
        for key in ["repository", "branch", "head", "origin", "operation", "changes", "staged_changes"]:
            self.assertIn(key, data)

    def test_modified_file_plan(self) -> None:
        fixture = self.fixture()
        write(fixture.repo / "src" / "app.txt", "changed\n")
        data = json.loads(ggcp(fixture.repo, "plan", "--json").stdout)
        self.assertEqual(len(data["entries"]), 1)
        self.assertEqual(data["entries"][0]["paths"], ["src/app.txt"])

    def test_multiple_modified_files_one_commit_each(self) -> None:
        fixture = self.fixture()
        write(fixture.repo / "src" / "app.txt", "changed\n")
        write(fixture.repo / "src" / "keep.txt", "changed\n")
        data = json.loads(ggcp(fixture.repo, "plan", "--json").stdout)
        self.assertEqual(len(data["entries"]), 2)

    def test_untracked_directory_expands(self) -> None:
        fixture = self.fixture()
        write(fixture.repo / "examples" / "basic.ts", "basic\n")
        write(fixture.repo / "examples" / "advanced.ts", "advanced\n")
        data = json.loads(ggcp(fixture.repo, "plan", "--json").stdout)
        self.assertEqual(len(data["entries"]), 2)

    def test_implementation_and_test_separate(self) -> None:
        fixture = self.fixture()
        write(fixture.repo / "src" / "lib" / "logger.ts", "export const logger = 1;\n")
        write(fixture.repo / "tests" / "logger.test.ts", "logger\n")
        data = json.loads(ggcp(fixture.repo, "plan", "--json").stdout)
        self.assertEqual(len(data["entries"]), 2)

    def test_delete_and_exact_rename(self) -> None:
        fixture = self.fixture()
        (fixture.repo / "src" / "keep.txt").unlink()
        (fixture.repo / "docs").mkdir()
        shutil.move(str(fixture.repo / "README.md"), str(fixture.repo / "docs" / "README.md"))
        data = json.loads(ggcp(fixture.repo, "plan", "--json").stdout)
        kinds = sorted(entry["kind"] for entry in data["entries"])
        self.assertEqual(kinds, ["delete", "rename"])

    def test_rename_with_modification(self) -> None:
        fixture = self.fixture()
        write(fixture.repo / "src" / "keep.txt", "\n".join(f"line {i}" for i in range(20)) + "\n")
        git(fixture.repo, "add", "--", "src/keep.txt")
        git(fixture.repo, "commit", "-m", "chore: prepare rename")
        git(fixture.repo, "push")
        (fixture.repo / "src" / "moved").mkdir()
        shutil.move(str(fixture.repo / "src" / "keep.txt"), str(fixture.repo / "src" / "moved" / "keep.txt"))
        with (fixture.repo / "src" / "moved" / "keep.txt").open("a", encoding="utf-8") as handle:
            handle.write("modified\n")
        data = json.loads(ggcp(fixture.repo, "plan", "--json").stdout)
        self.assertEqual(data["entries"][0]["kind"], "rename")

    def test_multiple_hunks_still_one_file_commit(self) -> None:
        fixture = self.fixture()
        write(fixture.repo / "src" / "app.txt", "one changed\n\n\nsecond changed\n")
        data = json.loads(ggcp(fixture.repo, "plan", "--json").stdout)
        self.assertEqual(len(data["entries"]), 1)

    def test_sensitive_blockers(self) -> None:
        for name in [".env.local", "credentials.json"]:
            fixture = self.fixture()
            write(fixture.repo / name, "example=value\n")
            result = ggcp(fixture.repo, "plan", "--json", check=False)
            self.assertEqual(result.returncode, 3)
            self.assertIn("SENSITIVE_PATH", result.stdout)

    def test_unrelated_staged_work_blocker(self) -> None:
        fixture = self.fixture()
        write(fixture.repo / "staged.txt", "staged\n")
        git(fixture.repo, "add", "--", "staged.txt")
        write(fixture.repo / "src" / "app.txt", "changed\n")
        result = ggcp(fixture.repo, "plan", "--json", check=False)
        self.assertEqual(result.returncode, 3)
        self.assertIn("STAGED_WORK", result.stdout)

    def test_non_main_branch(self) -> None:
        fixture = self.fixture(branch="feature/work")
        write(fixture.repo / "feature.txt", "feature\n")
        data = json.loads(ggcp(fixture.repo, "inspect", "--json").stdout)
        self.assertEqual(data["branch"], "feature/work")

    def test_no_remote_execute_stops_before_push(self) -> None:
        fixture = self.fixture(remote=False)
        write(fixture.repo / "new.txt", "new\n")
        result = ggcp(fixture.repo, "execute", "--yes", "--json", check=False)
        self.assertEqual(result.returncode, 3)
        self.assertIn("NO_REMOTE", result.stdout)

    def test_no_remote_no_push_creates_commits(self) -> None:
        fixture = self.fixture(remote=False)
        write(fixture.repo / "new.txt", "new\n")
        result = json.loads(ggcp(fixture.repo, "execute", "--yes", "--no-push", "--json").stdout)
        self.assertEqual(result["commits_created"], 1)

    def test_remote_ahead_and_successful_rebase(self) -> None:
        fixture = self.fixture()
        peer = fixture.temp / "peer"
        git(fixture.temp, "clone", "--branch", fixture.branch, str(fixture.remote), str(peer))
        git(peer, "config", "user.name", "Peer")
        git(peer, "config", "user.email", "peer@example.invalid")
        write(peer / "peer.txt", "peer\n")
        git(peer, "add", "--", "peer.txt")
        git(peer, "commit", "-m", "chore: peer")
        git(peer, "push")
        write(fixture.repo / "local.txt", "local\n")
        result = ggcp(fixture.repo, "execute", "--yes", "--json")
        self.assertEqual(result.returncode, 0)

    def test_rebase_conflict(self) -> None:
        fixture = self.fixture()
        peer = fixture.temp / "peer"
        git(fixture.temp, "clone", "--branch", fixture.branch, str(fixture.remote), str(peer))
        git(peer, "config", "user.name", "Peer")
        git(peer, "config", "user.email", "peer@example.invalid")
        write(peer / "src" / "app.txt", "remote\n")
        git(peer, "add", "--", "src/app.txt")
        git(peer, "commit", "-m", "chore: remote")
        git(peer, "push")
        write(fixture.repo / "src" / "app.txt", "local\n")
        result = ggcp(fixture.repo, "execute", "--yes", "--json", check=False)
        self.assertEqual(result.returncode, 6)

    def test_recover_detects_local_ahead(self) -> None:
        fixture = self.fixture()
        write(fixture.repo / "local.txt", "local\n")
        ggcp(fixture.repo, "execute", "--yes", "--no-push", "--json")
        data = json.loads(ggcp(fixture.repo, "recover", "--json").stdout)
        self.assertEqual(data["state"], "local_ahead")

    def test_recover_detects_remote_ahead(self) -> None:
        fixture = self.fixture()
        peer = fixture.temp / "peer"
        git(fixture.temp, "clone", "--branch", fixture.branch, str(fixture.remote), str(peer))
        git(peer, "config", "user.name", "Peer")
        git(peer, "config", "user.email", "peer@example.invalid")
        write(peer / "peer.txt", "peer\n")
        git(peer, "add", "--", "peer.txt")
        git(peer, "commit", "-m", "chore: peer")
        git(peer, "push")
        git(fixture.repo, "fetch", "origin")
        data = json.loads(ggcp(fixture.repo, "recover", "--json").stdout)
        self.assertEqual(data["state"], "remote_ahead")

    def test_recover_detects_diverged(self) -> None:
        fixture = self.fixture()
        peer = fixture.temp / "peer"
        git(fixture.temp, "clone", "--branch", fixture.branch, str(fixture.remote), str(peer))
        git(peer, "config", "user.name", "Peer")
        git(peer, "config", "user.email", "peer@example.invalid")
        write(peer / "peer.txt", "peer\n")
        git(peer, "add", "--", "peer.txt")
        git(peer, "commit", "-m", "chore: peer")
        git(peer, "push")
        write(fixture.repo / "local.txt", "local\n")
        ggcp(fixture.repo, "execute", "--yes", "--no-push", "--json")
        git(fixture.repo, "fetch", "origin")
        data = json.loads(ggcp(fixture.repo, "recover", "--json").stdout)
        self.assertEqual(data["state"], "diverged")

    def test_push_failure_after_commits_and_recover(self) -> None:
        fixture = self.fixture()
        hook = fixture.repo / ".git" / "hooks" / "pre-push"
        write(hook, "#!/bin/sh\nexit 1\n")
        if os.name != "nt":
            hook.chmod(0o755)
        write(fixture.repo / "new.txt", "new\n")
        result = ggcp(fixture.repo, "execute", "--yes", "--json", check=False)
        self.assertEqual(result.returncode, 5)
        recover = json.loads(ggcp(fixture.repo, "recover", "--json").stdout)
        self.assertIn(recover.get("state"), {"local_ahead", "no_upstream"})
        hook.unlink()
        retry = ggcp(fixture.repo, "execute", "--yes", "--json")
        self.assertEqual(json.loads(retry.stdout)["commits_created"], 0)

    def test_paths_with_spaces_and_unicode(self) -> None:
        fixture = self.fixture()
        write(fixture.repo / "space dir" / "hello file.txt", "hello\n")
        write(fixture.repo / "unicode" / "नमस्ते.txt", "hello\n")
        data = json.loads(ggcp(fixture.repo, "plan", "--json").stdout)
        self.assertEqual(len(data["entries"]), 2)

    def test_plan_output_validate_stale_and_mismatch(self) -> None:
        fixture = self.fixture()
        write(fixture.repo / "new.txt", "new\n")
        plan = fixture.temp / "plan.json"
        ggcp(fixture.repo, "plan", "--output", str(plan))
        ggcp(fixture.repo, "validate-plan", str(plan))
        write(fixture.repo / "other.txt", "other\n")
        self.assertEqual(ggcp(fixture.repo, "validate-plan", str(plan), check=False).returncode, 4)
        data = json.loads(plan.read_text(encoding="utf-8"))
        data["repository"] = str(fixture.temp / "elsewhere")
        plan.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(ggcp(fixture.repo, "validate-plan", str(plan), check=False).returncode, 4)

    def test_stale_plan_rejected_after_head_changes(self) -> None:
        fixture = self.fixture()
        write(fixture.repo / "new.txt", "new\n")
        plan = fixture.temp / "plan.json"
        ggcp(fixture.repo, "plan", "--output", str(plan))
        git(fixture.repo, "add", "--", "new.txt")
        git(fixture.repo, "commit", "-m", "chore: outside commit")
        self.assertEqual(ggcp(fixture.repo, "validate-plan", str(plan), check=False).returncode, 4)

    def test_execute_plan_file(self) -> None:
        fixture = self.fixture()
        write(fixture.repo / "new.txt", "new\n")
        plan = fixture.temp / "plan.json"
        ggcp(fixture.repo, "plan", "--output", str(plan))
        data = json.loads(plan.read_text(encoding="utf-8"))
        data["entries"][0]["message"] = "docs(new): add new file"
        plan.write_text(json.dumps(data), encoding="utf-8")
        result = json.loads(ggcp(fixture.repo, "execute", "--plan", str(plan), "--yes", "--no-push", "--json").stdout)
        self.assertEqual(result["commits_created"], 1)

    def test_dry_run_mutates_nothing_and_no_push(self) -> None:
        fixture = self.fixture()
        write(fixture.repo / "new.txt", "new\n")
        before = git(fixture.repo, "rev-parse", "HEAD").stdout
        ggcp(fixture.repo, "execute", "--dry-run", "--json")
        self.assertEqual(git(fixture.repo, "rev-parse", "HEAD").stdout, before)
        ggcp(fixture.repo, "execute", "--no-push", "--yes", "--json")
        status = git(fixture.repo, "status", "--branch", "--porcelain=v2").stdout
        self.assertIn("# branch.ab +1 -0", status)

    def test_full_execution_against_bare_remote(self) -> None:
        fixture = self.fixture()
        write(fixture.repo / "new.txt", "new\n")
        result = json.loads(ggcp(fixture.repo, "execute", "--yes", "--json").stdout)
        self.assertEqual(result["commits_created"], 1)
        self.assertIn("# branch.ab +0 -0", git(fixture.repo, "status", "--branch", "--porcelain=v2").stdout)

    def test_install_uninstall_copy(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ggcp-home-") as home:
            env = {**ENV, "USERPROFILE": home, "HOME": home}
            install = subprocess.run(
                [sys.executable, "-m", "granular_git_commit_push.cli", "install-skill", "--copy", "--json"],
                cwd=str(ROOT),
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(install.returncode, 0, install.stderr)
            target = Path(json.loads(install.stdout)["target"])
            self.assertTrue((target / "SKILL.md").exists())
            uninstall = subprocess.run(
                [sys.executable, "-m", "granular_git_commit_push.cli", "uninstall-skill", "--json"],
                cwd=str(ROOT),
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)

    def test_install_link_or_copy(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ggcp-home-") as home:
            env = {**ENV, "USERPROFILE": home, "HOME": home}
            result = subprocess.run(
                [sys.executable, "-m", "granular_git_commit_push.cli", "install-skill", "--link", "--json"],
                cwd=str(ROOT),
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(json.loads(result.stdout)["type"], {"link", "copy"})

    def test_status_recover_compatibility_json(self) -> None:
        fixture = self.fixture()
        self.assertIn("clean", json.loads(ggcp(fixture.repo, "status", "--json").stdout))
        self.assertIn("state", json.loads(ggcp(fixture.repo, "recover", "--json").stdout))
        self.assertIn("agents", json.loads(ggcp(fixture.repo, "compatibility", "--json").stdout))

    def test_known_ten_commit_regression(self) -> None:
        fixture = self.fixture()
        write(fixture.repo / "src" / "App.tsx", "app\n")
        write(fixture.repo / "src" / "components" / "Header.tsx", "header\n")
        write(fixture.repo / "docs" / "INSTALL.md", "install\n")
        write(fixture.repo / "docs" / "RELEASE.md", "release\n")
        git(fixture.repo, "add", "--", "src/App.tsx", "src/components/Header.tsx", "docs/INSTALL.md", "docs/RELEASE.md")
        git(fixture.repo, "commit", "-m", "chore: prepare ten fixture")
        git(fixture.repo, "push")
        write(fixture.repo / "README.md", "readme changed\n")
        write(fixture.repo / "src" / "App.tsx", "app changed\n")
        write(fixture.repo / "src" / "components" / "Header.tsx", "header changed\n")
        write(fixture.repo / "src" / "lib" / "logger.ts", "logger\n")
        write(fixture.repo / "tests" / "logger.test.ts", "test\n")
        (fixture.repo / "docs" / "guides").mkdir(parents=True)
        shutil.move(str(fixture.repo / "docs" / "INSTALL.md"), str(fixture.repo / "docs" / "guides" / "INSTALL.md"))
        (fixture.repo / "docs" / "RELEASE.md").unlink()
        write(fixture.repo / "examples" / "README.md", "examples\n")
        write(fixture.repo / "examples" / "basic.ts", "basic\n")
        write(fixture.repo / "examples" / "advanced.ts", "advanced\n")
        data = json.loads(ggcp(fixture.repo, "plan", "--json").stdout)
        self.assertEqual(len(data["entries"]), 10)


if __name__ == "__main__":
    unittest.main()
