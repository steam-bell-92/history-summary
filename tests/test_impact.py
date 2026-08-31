import unittest

from src.impact import assess_risk, detect_domain_findings, merge_domain_findings
from src.models import Commit, DomainFinding, FileChange


def make_commit(hash_="abc1234", insertions=0, deletions=0, files_changed=0):
    return Commit(
        hash=hash_,
        author="Alice",
        date="2026-08-01T00:00:00+00:00",
        message="change",
        insertions=insertions,
        deletions=deletions,
        files_changed=files_changed,
    )


class DomainFindingTests(unittest.TestCase):
    def test_unrelated_filename_does_not_trigger_authentication(self):
        findings = detect_domain_findings("update author bios", [FileChange(path="src/authors.py")])
        self.assertEqual(findings, [])

    def test_path_based_evidence_is_high_confidence(self):
        findings = detect_domain_findings("refactor internals", [FileChange(path="src/auth/session.py")])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].domain, "Authentication")
        self.assertEqual(findings[0].confidence, "High")
        self.assertTrue(any("paths:" in item for item in findings[0].evidence))

    def test_message_only_evidence_is_medium_confidence(self):
        findings = detect_domain_findings("improve oauth handling", [FileChange(path="src/unrelated.py")])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].domain, "Authentication")
        self.assertEqual(findings[0].confidence, "Medium")

    def test_generated_files_are_never_used_as_evidence(self):
        findings = detect_domain_findings(
            "regenerate build output",
            [FileChange(path="build/api/routes.py", is_generated=True, exclude_pattern="build/*")],
        )
        self.assertEqual(findings, [])

    def test_merge_domain_findings_deduplicates_and_promotes_confidence(self):
        per_commit = [
            DomainFinding(domain="Authentication", evidence=["commit message terms: oauth"], confidence="Medium"),
            DomainFinding(domain="Authentication", evidence=["paths: src/auth/session.py"], confidence="High"),
        ]
        merged = merge_domain_findings(per_commit)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].confidence, "High")
        self.assertEqual(len(merged[0].evidence), 2)


class RiskAssessmentTests(unittest.TestCase):
    def test_no_findings_and_small_changes_is_low_risk(self):
        commits = [make_commit(insertions=5, deletions=2, files_changed=1)]
        risk = assess_risk([], commits)
        self.assertEqual(risk.level, "Low")

    def test_high_confidence_auth_with_large_diff_is_high_risk(self):
        findings = [DomainFinding(domain="Authentication", evidence=["paths: src/auth/session.py"], confidence="High")]
        commits = [make_commit(insertions=150, deletions=100, files_changed=2)]
        risk = assess_risk(findings, commits)
        self.assertEqual(risk.level, "High")
        self.assertTrue(any("Authentication" in reason for reason in risk.reasons))

    def test_high_confidence_auth_with_small_diff_is_medium_risk(self):
        findings = [DomainFinding(domain="Authentication", evidence=["paths: src/auth/session.py"], confidence="High")]
        commits = [make_commit(insertions=5, deletions=2, files_changed=1)]
        risk = assess_risk(findings, commits)
        self.assertEqual(risk.level, "Medium")

    def test_three_or_more_domains_without_high_risk_domain_is_medium(self):
        findings = [
            DomainFinding(domain="API", evidence=["paths: src/api/routes.py"], confidence="High"),
            DomainFinding(domain="Frontend", evidence=["paths: src/ui/page.tsx"], confidence="High"),
            DomainFinding(domain="Tests", evidence=["paths: tests/test_api.py"], confidence="High"),
        ]
        commits = [make_commit(insertions=5, deletions=2, files_changed=1)]
        risk = assess_risk(findings, commits)
        self.assertEqual(risk.level, "Medium")

    def test_broad_file_spread_alone_is_medium_risk(self):
        commits = [make_commit(insertions=10, deletions=5, files_changed=6)]
        risk = assess_risk([], commits)
        self.assertEqual(risk.level, "Medium")

    def test_risk_uses_cautious_language(self):
        findings = [DomainFinding(domain="Database", evidence=["paths: src/db/schema.py"], confidence="High")]
        commits = [make_commit(insertions=5, deletions=2, files_changed=1)]
        risk = assess_risk(findings, commits)
        joined_reasons = " ".join(risk.reasons).lower()
        self.assertTrue(any(phrase in joined_reasons for phrase in ("may affect", "review recommended", "potential impact")))


if __name__ == "__main__":
    unittest.main()
