import subprocess
import tempfile
import unittest
from pathlib import Path

from src.git_engine import build_analysis


class ScenarioTestCase(unittest.TestCase):
    """Base class providing a throwaway git repository per test."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        self._git("init")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test User")

    def tearDown(self):
        self._tmp.cleanup()

    def _git(self, *args: str) -> None:
        subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True, text=True)

    def commit_all(self, message: str) -> None:
        self._git("add", "-A")
        self._git("commit", "-m", message)

    def write(self, relative_path: str, content: str = "content\n") -> None:
        path = self.repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


class DocumentationOnlyScenarioTests(ScenarioTestCase):
    def test_docs_only_repository_is_classified_as_documentation(self):
        self.write("README.md", "# Title\n")
        self.commit_all("initial")
        self.write("docs/guide.md", "guide content\n")
        self.commit_all("docs: add usage guide")

        result = build_analysis(self.repo, "HEAD~1..HEAD")

        self.assertEqual(result.categories, {"Documentation": 1})
        self.assertIn("Documentation", {finding.domain for finding in result.domain_findings})
        self.assertEqual(result.risk.level, "Low")


class TestsOnlyScenarioTests(ScenarioTestCase):
    def test_tests_only_repository_is_classified_as_test(self):
        self.write("src/app.py", "def add(a, b):\n    return a + b\n")
        self.commit_all("initial")
        self.write("tests/test_app.py", "def test_add():\n    assert True\n")
        self.commit_all("test: add unit test for add()")

        result = build_analysis(self.repo, "HEAD~1..HEAD")

        self.assertEqual(result.categories, {"Test": 1})
        self.assertIn("Tests", {finding.domain for finding in result.domain_findings})


class CodeChangeScenarioTests(ScenarioTestCase):
    def test_code_only_repository_is_classified_as_feature_or_bug_fix(self):
        self.write("src/app.py", "def add(a, b):\n    return a + b\n")
        self.commit_all("initial")
        self.write("src/app.py", "def add(a, b):\n    return a + b + 0\n")
        self.commit_all("feat: tweak add implementation")

        result = build_analysis(self.repo, "HEAD~1..HEAD")

        self.assertEqual(result.categories, {"Feature": 1})
        self.assertEqual(result.changed_areas, {"src": 1})


class EmptyAndInvalidRangeScenarioTests(ScenarioTestCase):
    def test_empty_repository_returns_empty_analysis(self):
        result = build_analysis(self.repo, "HEAD")
        self.assertEqual(result.commit_count, 0)
        self.assertEqual(result.summary, "No commit history is available for the selected range.")
        self.assertEqual(result.risk.level, "Low")

    def test_invalid_revision_range_raises(self):
        self.write("file.txt")
        self.commit_all("initial")
        with self.assertRaises(RuntimeError):
            build_analysis(self.repo, "not-a-ref..HEAD")


class GeneratedArtifactScenarioTests(ScenarioTestCase):
    def test_generated_artifacts_are_excluded_but_reported(self):
        self.write("src/app.py", "print(1)\n")
        self.commit_all("initial")
        self.write("gitlens_zero.egg-info/PKG-INFO", "Metadata-Version: 2.1\n")
        self.write("build/lib/app.py", "print(1)\n")
        self.write("__pycache__/app.cpython-312.pyc", "binary\n")
        self.write("src/app.py", "print(2)\n")
        self.commit_all("chore: rebuild artifacts and tweak app")

        result = build_analysis(self.repo, "HEAD~1..HEAD")

        self.assertNotIn("gitlens_zero.egg-info/PKG-INFO", result.hotspots)
        self.assertNotIn("build/lib/app.py", result.hotspots)
        self.assertNotIn("__pycache__/app.cpython-312.pyc", result.hotspots)
        self.assertIn("src/app.py", result.hotspots)

        excluded_paths = {excluded.path for excluded in result.excluded_files}
        self.assertIn("gitlens_zero.egg-info/PKG-INFO", excluded_paths)
        self.assertIn("build/lib/app.py", excluded_paths)
        self.assertIn("__pycache__/app.cpython-312.pyc", excluded_paths)

    def test_include_generated_flag_disables_exclusion(self):
        self.write("src/app.py", "print(1)\n")
        self.commit_all("initial")
        self.write("build/lib/app.py", "print(1)\n")
        self.commit_all("chore: rebuild artifacts")

        result = build_analysis(self.repo, "HEAD~1..HEAD", include_generated=True)

        self.assertIn("build/lib/app.py", result.hotspots)

    def test_custom_exclude_pattern_is_applied(self):
        self.write("src/app.py", "print(1)\n")
        self.commit_all("initial")
        self.write("data/schema.generated.json", "{}\n")
        self.commit_all("chore: regenerate schema")

        result = build_analysis(self.repo, "HEAD~1..HEAD", exclude_patterns=["*.generated.json"])

        self.assertNotIn("data/schema.generated.json", result.hotspots)
        excluded_paths = {excluded.path for excluded in result.excluded_files}
        self.assertIn("data/schema.generated.json", excluded_paths)


if __name__ == "__main__":
    unittest.main()
