import subprocess
import tempfile
import unittest
from pathlib import Path

from src.git_engine import build_analysis, get_commit_changes
from src.impact import detect_change_domains
from src.models import FileChange


class GitEngineIntegrationTests(unittest.TestCase):
    def run_git(self, repo: Path, *args: str) -> None:
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)

    def test_structured_git_parsing_handles_renames_deletes_binary_and_spaces(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self.run_git(repo, "init")
            self.run_git(repo, "config", "user.email", "test@example.com")
            self.run_git(repo, "config", "user.name", "Test User")

            (repo / "hello world.txt").write_text("one\n", encoding="utf-8")
            (repo / "docs").mkdir()
            (repo / "docs" / "readme.md").write_text("doc\n", encoding="utf-8")
            (repo / "bin.dat").write_bytes(bytes([1, 2, 3]))
            self.run_git(repo, "add", ".")
            self.run_git(repo, "commit", "-m", "initial")

            (repo / "hello world.txt").rename(repo / "hello renamed.txt")
            (repo / "docs" / "readme.md").unlink()
            (repo / "new file.py").write_text("print(1)\n", encoding="utf-8")
            (repo / "bin.dat").write_bytes(bytes([1, 2, 3, 4]))
            self.run_git(repo, "add", "-A")
            self.run_git(repo, "commit", "-m", "second")

            changes = get_commit_changes(repo, "HEAD")
            self.assertEqual(len(changes), 4)
            self.assertTrue(any(change.path == "hello renamed.txt" and change.old_path == "hello world.txt" for change in changes))
            self.assertTrue(any(change.path == "docs/readme.md" and change.status == "D" for change in changes))
            self.assertTrue(any(change.path == "new file.py" for change in changes))
            self.assertTrue(any(change.path == "bin.dat" for change in changes))

            analysis = build_analysis(repo, "HEAD~1..HEAD")
            self.assertEqual(analysis.commit_count, 1)
            self.assertEqual(analysis.commits[0].files_changed, 4)
            self.assertIn("hello world.txt", analysis.hotspots)
            self.assertIn("hello renamed.txt", analysis.hotspots)
            self.assertIn("new file.py", analysis.hotspots)

    def test_invalid_revision_range_raises_instead_of_falling_back(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self.run_git(repo, "init")
            self.run_git(repo, "config", "user.email", "test@example.com")
            self.run_git(repo, "config", "user.name", "Test User")

            (repo / "file.txt").write_text("content\n", encoding="utf-8")
            self.run_git(repo, "add", ".")
            self.run_git(repo, "commit", "-m", "initial")

            with self.assertRaises(RuntimeError):
                build_analysis(repo, "not-a-ref..HEAD")

    def test_empty_repository_returns_empty_analysis(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self.run_git(repo, "init")
            self.run_git(repo, "config", "user.email", "test@example.com")
            self.run_git(repo, "config", "user.name", "Test User")

            analysis = build_analysis(repo, "HEAD")

            self.assertEqual(analysis.commit_count, 0)
            self.assertEqual(analysis.summary, "No commit history is available for the selected range.")


class ImpactDetectionTests(unittest.TestCase):
    def test_unrelated_filename_does_not_trigger_authentication(self):
        domains, reasons = detect_change_domains("update author bios", [FileChange(path="src/authors.py")])
        self.assertEqual(domains, [])
        self.assertEqual(reasons, [])


if __name__ == "__main__":
    unittest.main()
