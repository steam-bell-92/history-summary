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


if __name__ == "__main__":
    unittest.main()
