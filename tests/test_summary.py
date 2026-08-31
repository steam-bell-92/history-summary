import unittest

from src.models import AnalysisResult, Commit
from src.summary import generate_summary


def make_commit(hash_, author, insertions, deletions, files_changed):
    return Commit(
        hash=hash_,
        author=author,
        date="2026-08-01T00:00:00+00:00",
        message="change",
        insertions=insertions,
        deletions=deletions,
        files_changed=files_changed,
    )


class SummaryTests(unittest.TestCase):
    def test_generate_summary_uses_actual_statistics(self):
        commits = [
            make_commit("a1", "Alice", 20, 5, 2),
            make_commit("a2", "Bob", 10, 2, 3),
            make_commit("a3", "Alice", 5, 1, 1),
        ]
        result = AnalysisResult(
            commit_count=3,
            contributors=["Alice", "Bob"],
            categories={"Feature": 2, "Bug Fix": 1},
            hotspots={"src/auth.py": 3, "src/api.py": 2},
            changed_areas={"src": 5},
            commits=commits,
        )
        summary = generate_summary(result)
        self.assertIn("3 commit(s)", summary)
        self.assertIn("Alice", summary)
        self.assertIn("Bob", summary)
        self.assertIn("+35/-8", summary)
        self.assertIn("Feature", summary)
        self.assertIn("src/auth.py", summary)
        self.assertIn("src", summary)

    def test_generate_summary_never_invents_a_narrative_subject(self):
        commits = [make_commit("a1", "Alice", 1, 0, 1)]
        result = AnalysisResult(
            commit_count=1,
            contributors=["Alice"],
            hotspots={"src/auth.py": 1},
            commits=commits,
        )
        summary = generate_summary(result)
        # The summary should stick to observed stats and not editorialize about
        # what the change was "about" (that belongs to the heuristic domain
        # findings elsewhere, not the fact-based summary).
        self.assertNotIn("focus", summary.lower())
        self.assertNotIn("appeared to", summary.lower())

    def test_generate_summary_reports_excluded_files_count(self):
        from src.models import ExcludedFile

        commits = [make_commit("a1", "Alice", 1, 0, 1)]
        result = AnalysisResult(
            commit_count=1,
            contributors=["Alice"],
            commits=commits,
            excluded_files=[ExcludedFile(path="build/out.txt", pattern="build/*")],
        )
        summary = generate_summary(result)
        self.assertIn("1 generated/build artifact", summary)

    def test_empty_range_summary(self):
        result = AnalysisResult(commit_count=0)
        summary = generate_summary(result)
        self.assertEqual(summary, "No commit history is available for the selected range.")


if __name__ == "__main__":
    unittest.main()
