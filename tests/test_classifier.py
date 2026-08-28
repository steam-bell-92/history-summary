import unittest

from src.classifier import classify_commit


class ClassifierTests(unittest.TestCase):
    def test_feature_commit(self):
        result = classify_commit("feat(auth): add JWT validation", "+token = verify(jwt)\n+login(request)")
        self.assertEqual(result, "Feature")

    def test_bugfix_commit(self):
        result = classify_commit("fix: handle null session", "+if session is None:\n-raise ValueError")
        self.assertEqual(result, "Bug Fix")

    def test_docs_commit(self):
        result = classify_commit("docs: update API guide", "+# API guide\n+usage examples")
        self.assertEqual(result, "Documentation")

    def test_configuration_commit(self):
        result = classify_commit("chore: update settings", "+DATABASE_URL=prod\n+DEBUG=false")
        self.assertEqual(result, "Configuration")


if __name__ == "__main__":
    unittest.main()
