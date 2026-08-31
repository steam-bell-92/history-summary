from __future__ import annotations

import re

from .models import Commit, DomainFinding, FileChange, RiskAssessment

# Keyword sets used to detect which engineering domain a change plausibly touches.
# This is a heuristic interpretation layer: it does NOT claim a file/area was
# changed (that is a fact, see changed_areas) -- it claims that, based on
# naming conventions, the change *may* relate to a particular part of the
# system. Every finding carries evidence and a confidence level so a reader
# can judge how much to trust it.
DOMAIN_PATTERNS: dict[str, list[str]] = {
    "Authentication": ["auth", "login", "session", "token", "oauth", "jwt", "permission"],
    "Database": ["db", "database", "schema", "migration", "sql", "orm", "table"],
    "API": ["api", "endpoint", "route", "http", "rest", "request", "response"],
    "Frontend": ["frontend", "ui", "react", "template", "css", "html", "component", "page"],
    "Tests": ["test", "tests", "spec", "pytest", "unit", "assert", "integration"],
    "Documentation": ["doc", "readme", "guide", "markdown", "docs"],
}

# Domains where an incorrect or incomplete change carries outsized operational
# risk (security exposure, data loss/corruption). This set intentionally does
# NOT include Tests, Documentation, Frontend, or API, since regressions there
# are typically lower-stakes and more visible/recoverable.
HIGH_RISK_DOMAINS = {"Authentication", "Database"}

# Thresholds used by assess_risk(). Kept as named constants so the formula in
# assess_risk() stays legible and the numbers are easy to find and adjust.
LARGE_DIFF_THRESHOLD = 200  # combined additions + deletions in a single commit
WIDE_CHANGE_THRESHOLD = 5  # files touched in a single commit
MANY_COMMITS_THRESHOLD = 10  # commits in the analyzed range


def detect_domain_findings(message: str, changes: list[FileChange]) -> list[DomainFinding]:
    """Detect engineering domains a single commit may affect, with evidence and confidence.

    Path-based evidence is treated as High confidence, because a changed path
    reflects an actual structural change. Commit-message wording alone is
    treated as Medium confidence, since message text can be loosely worded,
    aspirational, or unrelated to the actual diff. Changes flagged as
    generated/build artifacts are never used as evidence.
    """
    message_tokens = _tokenize(message)
    findings: list[DomainFinding] = []

    for domain, terms in DOMAIN_PATTERNS.items():
        matched_paths = sorted(
            {
                change.path
                for change in changes
                if not change.is_generated
                and (_path_matches(change.path, terms) or _path_matches(change.old_path or "", terms))
            }
        )
        matched_terms = sorted({term for term in terms if term.lower() in message_tokens})

        if not matched_paths and not matched_terms:
            continue

        evidence: list[str] = []
        if matched_paths:
            evidence.append(f"paths: {', '.join(matched_paths)}")
        if matched_terms:
            evidence.append(f"commit message terms: {', '.join(matched_terms)}")

        findings.append(
            DomainFinding(
                domain=domain,
                evidence=evidence,
                confidence="High" if matched_paths else "Medium",
            )
        )

    return findings


def merge_domain_findings(per_commit_findings: list[DomainFinding]) -> list[DomainFinding]:
    """Combine per-commit domain findings into one deduplicated list, preserving evidence.

    When the same domain is found in multiple commits, evidence is unioned and
    the confidence is promoted to High if any contributing commit had
    path-based (High confidence) evidence.
    """
    merged: dict[str, DomainFinding] = {}
    for finding in per_commit_findings:
        existing = merged.get(finding.domain)
        if existing is None:
            merged[finding.domain] = DomainFinding(
                domain=finding.domain, evidence=list(finding.evidence), confidence=finding.confidence
            )
            continue
        for item in finding.evidence:
            if item not in existing.evidence:
                existing.evidence.append(item)
        if finding.confidence == "High":
            existing.confidence = "High"

    return [merged[domain] for domain in sorted(merged)]


def assess_risk(domain_findings: list[DomainFinding], commits: list[Commit] | None = None) -> RiskAssessment:
    """Derive a qualitative Low/Medium/High potential-impact rating.

    This uses an explicit, documented formula rather than an opaque numeric
    score. Rules are evaluated in order; the first match determines the level:

      HIGH   A high-risk domain (Authentication or Database) has at least one
             High-confidence (path-based) finding, AND the change is large
             (>{LARGE_DIFF_THRESHOLD} combined additions/deletions in a single
             commit) or broad (>={WIDE_CHANGE_THRESHOLD} files touched in a
             single commit).

      MEDIUM Any of the following: a high-risk domain was detected at all
             (even Medium confidence); a single commit is large or broad on
             its own; three or more distinct engineering domains were
             affected across the range.

      LOW    None of the above conditions were met.

    A separate ``confidence`` field reflects how much of the *evidence behind
    the rating itself* rests on structural (path-based) signals versus
    commit-message wording or commit counts alone.

    Language throughout is deliberately cautious ("may affect", "potential
    impact") -- this is an interpretation of patterns, not a certified
    outcome, and review is always recommended.
    """
    commits = commits or []
    domains_by_name = {finding.domain: finding for finding in domain_findings}

    large_commits = [commit for commit in commits if (commit.insertions + commit.deletions) > LARGE_DIFF_THRESHOLD]
    wide_commits = [commit for commit in commits if commit.files_changed >= WIDE_CHANGE_THRESHOLD]
    many_commits = len(commits) >= MANY_COMMITS_THRESHOLD

    high_risk_hits = [domains_by_name[name] for name in HIGH_RISK_DOMAINS if name in domains_by_name]
    high_risk_high_confidence = [finding for finding in high_risk_hits if finding.confidence == "High"]

    reasons: list[str] = []

    if high_risk_high_confidence and (large_commits or wide_commits):
        level = "High"
        domain_names = ", ".join(sorted(finding.domain for finding in high_risk_high_confidence))
        reasons.append(
            f"High-confidence (path-based) changes were detected in {domain_names}, "
            "a domain where mistakes are costly to recover from -- review recommended."
        )
        reasons.extend(_diff_size_reasons(large_commits, wide_commits))
    elif high_risk_hits or large_commits or wide_commits or len(domains_by_name) >= 3:
        level = "Medium"
        if high_risk_hits:
            domain_names = ", ".join(sorted(finding.domain for finding in high_risk_hits))
            reasons.append(f"Changes may affect {domain_names}; potential impact should be reviewed.")
        reasons.extend(_diff_size_reasons(large_commits, wide_commits))
        if len(domains_by_name) >= 3:
            reasons.append(
                f"Multiple engineering domains were potentially affected: {', '.join(sorted(domains_by_name))}."
            )
    else:
        level = "Low"
        reasons.append("No high-risk domains, large diffs, or broad file spreads were detected.")

    if many_commits:
        reasons.append(
            f"The range contains {len(commits)} commits (>= {MANY_COMMITS_THRESHOLD}), which widens the review surface."
        )

    if large_commits or wide_commits or high_risk_high_confidence:
        confidence = "High"
    elif domain_findings:
        confidence = "Medium"
    else:
        confidence = "Low"

    return RiskAssessment(level=level, reasons=reasons, confidence=confidence)


def _diff_size_reasons(large_commits: list[Commit], wide_commits: list[Commit]) -> list[str]:
    reasons: list[str] = []
    if large_commits:
        hashes = ", ".join(commit.hash[:7] for commit in large_commits)
        reasons.append(f"Large diff volume (> {LARGE_DIFF_THRESHOLD} combined lines) in commit(s): {hashes}.")
    if wide_commits:
        hashes = ", ".join(commit.hash[:7] for commit in wide_commits)
        reasons.append(f"Broad file spread (>= {WIDE_CHANGE_THRESHOLD} files) in commit(s): {hashes}.")
    return reasons


def _path_matches(path: str, terms: list[str]) -> bool:
    tokens = _tokenize(path)
    return any(term.lower() in tokens for term in terms)


def _tokenize(text: str) -> set[str]:
    normalized = text.replace("\\", "/").lower()
    normalized = re.sub(r"([a-z])([A-Z])", r"\1 \2", normalized)
    return {token for token in re.split(r"[^a-z0-9]+", normalized) if token}
