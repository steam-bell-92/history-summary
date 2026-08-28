import unittest

from src.models import AnalysisResult
from src.summary import generate_summary


class SummaryTests(unittest.TestCase):
    def test_generate_summary(self):
        result = AnalysisResult(
            commit_count=5,
            contributors=["Alice", "Bob"],
            categories={"Feature": 3, "Bug Fix": 2},
            hotspots={"src/auth.py": 3, "src/api.py": 2},
            impact_score=7,
            summary="Focus on authentication and API changes.",
        )
        summary = generate_summary(result)
        self.assertIn("5 commits", summary)
        self.assertIn("authentication", summary.lower())
        self.assertIn("Alice", summary)


if __name__ == "__main__":
    unittest.main()
