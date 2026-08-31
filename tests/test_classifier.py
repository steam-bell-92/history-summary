import unittest

from src.classifier import classify_commit
from src.models import FileChange


class ClassifierTests(unittest.TestCase):
    def test_feature_commit(self):
        result = classify_commit("feat(auth): add JWT validation", [FileChange(path="src/auth/session_manager.py")])
        self.assertEqual(result, "Security")

    def test_bugfix_commit(self):
        result = classify_commit("fix: handle null session", "+if session is None:\n-raise ValueError")
        self.assertEqual(result, "Bug Fix")

    def test_docs_commit(self):
        result = classify_commit("docs: update API guide", [FileChange(path="docs/api-guide.md")])
        self.assertEqual(result, "Documentation")

    def test_configuration_commit(self):
        result = classify_commit("chore: update settings", [FileChange(path="pyproject.toml")])
        self.assertEqual(result, "Configuration")

    def test_unrelated_filename_does_not_trigger_authentication(self):
        result = classify_commit("update author bios", [FileChange(path="src/authors.py")])
        self.assertEqual(result, "Feature")

    def test_build_artifacts_only_commit_is_classified_separately(self):
        changes = [
            FileChange(path="gitlens_zero.egg-info/PKG-INFO", is_generated=True, exclude_pattern="*.egg-info/*"),
            FileChange(path="build/lib/foo.py", is_generated=True, exclude_pattern="build/*"),
        ]
        result = classify_commit("chore: regenerate build output", changes)
        self.assertEqual(result, "Build Artifacts")

    def test_mixed_generated_and_substantive_changes_uses_substantive_only(self):
        changes = [
            FileChange(path="gitlens_zero.egg-info/PKG-INFO", is_generated=True, exclude_pattern="*.egg-info/*"),
            FileChange(path="docs/guide.md", is_generated=False),
        ]
        result = classify_commit("update packaging metadata", changes)
        self.assertEqual(result, "Documentation")


if __name__ == "__main__":
    unittest.main()
