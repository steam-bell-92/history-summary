# GitLens Zero

GitLens Zero is a zero-dependency Python CLI that inspects a Git repository and turns commit history into clear, evidence-based project insights. The application uses Git on the command line and Python's standard library only, so it stays compliant with the Zero Dependency Hackathon requirement.

## Project Overview

This tool analyzes a repository's commit history to produce:

- commit and line statistics (commits, files, additions, deletions)
- contributor summaries
- file hotspot and changed-area analysis
- commit classification (pattern-based, labeled as "detected")
- heuristic engineering-domain findings, each with evidence and a confidence level
- a qualitative, explainable potential-impact rating (Low / Medium / High)
- transparent generated/build artifact detection and exclusion
- fact-based, stats-driven narrative summaries
- standalone HTML reporting
- JSON output for scripting

## Analytical Model: Facts, Detected Changes, Heuristics, and Potential Impact

A core design goal of this tool is to never conflate "a file changed" with "an
engineering domain was affected" with "this is risky." Every result is
grouped into one of four kinds of claim, and the CLI and HTML report label
each accordingly:

| Layer | What it means | Where it comes from |
| --- | --- | --- |
| **Facts** | Directly observed from Git output. Cannot be wrong. | `commit_count`, `contributors`, `hotspots`, `changed_areas`, per-commit `insertions`/`deletions`/`files_changed` |
| **Detected changes** | Pattern-based classification of the diff/message shape. | `categories` (Feature, Bug Fix, Refactor, Documentation, Test, Configuration, Security, Build Artifacts) |
| **Heuristic interpretation** | An inference about which part of the *system* (not just which files) may be affected, with evidence and a confidence level. | `domain_findings` (Authentication, Database, API, Frontend, Tests, Documentation) |
| **Potential impact** | A qualitative, explainable risk rating derived from an explicit formula over the layers above. Never a bare number. | `risk` (level, reasons, confidence) |

### Risk formula

`risk.level` is computed by `impact.assess_risk()` using this explicit,
documented rule (evaluated top to bottom, first match wins):

- **High** -- a high-risk domain (Authentication or Database) has at least one
  High-confidence (path-based) finding, **and** the change is large (more
  than 200 combined added/deleted lines in a single commit) or broad (5 or
  more files touched in a single commit).
- **Medium** -- a high-risk domain was detected at all (any confidence), OR a
  single commit is large/broad on its own, OR three or more distinct
  engineering domains were affected across the range.
- **Low** -- none of the above.

`risk.confidence` separately reflects how much of the *evidence behind the
rating* rests on structural (path-based) signals versus commit-message
wording or commit counts alone. `risk.reasons` always spells out exactly
which condition fired and lists the specific commits/domains involved, using
cautious language ("may affect", "potential impact", "review recommended")
rather than asserting certainty.

## Generated/Build Artifact Handling

Common generated and build outputs -- `*.egg-info`, `build/`, `dist/`,
`__pycache__`, `.pytest_cache`, `.mypy_cache`, `.tox`, `node_modules/`,
`.venv`/`venv`, `*.pyc`, `*.egg`, `*.min.js`, `*.map`, and a few others (see
`src/excludes.py` for the full list) -- are excluded from hotspot,
classification, and domain analysis **by default**, but never silently:

- Every excluded file, and the exact pattern that matched it, is listed in
  `AnalysisResult.excluded_files` and rendered in its own report section
  ("Excluded Generated/Build Artifacts").
- A commit whose only changes are generated artifacts is classified as
  `Build Artifacts` rather than being folded into another category.
- `--exclude PATTERN` (repeatable) adds extra glob patterns on top of the
  built-in defaults, e.g. `--exclude "*.generated.json"`.
- `--include-generated` disables exclusion entirely, so every changed file is
  treated as substantive.

## Features

- Range-based analysis: `HEAD~10..HEAD`, `main..feature-auth`, and similar Git revision ranges
- Commit statistics for additions, deletions, and files changed
- Contributor identification across the selected history window
- Commit classification into Feature, Bug Fix, Refactor, Documentation, Test, Configuration, Security, and HEADBuild Artifacts
- Heuristic engineering-domain detection for Authentication, Database, API, Frontend, Tests, and Documentation, each with evidence and a confidence level
- A qualitative, explainable Low/Medium/High potential-impact rating (see formula above) instead of an opaque numeric score
- Transparent generated/build artifact detection with a documented, overridable exclusion mechanism
- HTML dashboard report generation with no JavaScript libraries, with Facts / Detected Changes / Heuristic Interpretation / Potential Impact clearly labeled
- JSON output (`--json`) for scripting and further processing
- Strict zero-dependency runtime design using the Python standard library only

## Installation

1. Ensure Python 3.12+ is installed.
2. Ensure Git is installed and available on your `PATH`.
3. Clone the repository and open the project root.
4. Run the CLI as follows:

```bash
python -m src.main analyze HEAD~3..
python -m src.main stats main..feature-auth
python -m src.main report HEAD~3..HEAD --html reports/history.html
python -m src.main version
```

## Usage Examples

```bash
gitlens analyze HEAD~3..HEAD
gitlens analyze HEAD~3..HEAD --json
gitlens analyze HEAD~3..HEAD --exclude "*.generated.json"
gitlens analyze HEAD~3..HEAD --include-generated
gitlens stats main..feature-auth
gitlens report main..feature-auth --html reports/history.html --open
gitlens version
```

## Architecture

```text
Git Repository
      |
Git CLI (subprocess)
      |
Commit Parser (structured, null-byte-delimited)
      |
Generated/Build Artifact Exclusion (transparent, documented)
      |
Classifier (Detected changes)              Impact Engine (Heuristic domains + Potential-impact rating)
      |                                             |
      +---------------------+----------------------+
                             |
                    Summary Generator (fact-based)
                             |
                    CLI + JSON + HTML Report
```

## Screenshots Placeholder

![GitLens Zero Dashboard Placeholder](https://github.com/steam-bell-92/history-summary/blob/1e124e4f8f48fb09478a2dbaaa38f779d195c669/git.png)

## Zero Dependency Explanation

This project intentionally avoids all third-party runtime packages, including GitPython, Click, Rich, Requests, Pandas, Jinja2, and Flask. Instead, it uses:

- argparse for command parsing
- subprocess for Git execution
- pathlib for file and directory handling
- re for diff, commit, and path-token parsing
- fnmatch for generated/build artifact glob matching
- collections for counting and grouping
- html for safe HTML escaping
- dataclasses for typed models
- json for machine-readable output
- webbrowser for opening the generated report
- unittest for testing

See `STDLIB.md` for the full dependency-to-stdlib mapping.

## Testing

Run the full suite with:

```bash
python -m unittest discover -s tests
```

Coverage includes: structured Git parsing (renames, deletions, binary files,
filenames with spaces), invalid/empty revision ranges, generated/build
artifact detection and exclusion (including `--exclude` and
`--include-generated`), commit classification (including the `Build
Artifacts` category), domain-finding confidence levels, the risk formula's
Low/Medium/High branches, and fact-based summary generation.

## Future Roadmap

- Add branch comparison summaries
- Add local SQLite caching for large histories
- Extend HTML styling and dashboard sections
- Allow configurable domain pattern sets for project-specific vocabularies

## License

MIT
