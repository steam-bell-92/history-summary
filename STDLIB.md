# Standard Library Replacements for Zero-Dependency Git Analysis

This project intentionally avoids third-party packages. The table below
lists only techniques actually used in `src/` today, matched to the
common third-party dependency each one replaces, so this file doesn't drift
from the real implementation.

| Common Dependency | Replacement actually used here | Where | Why it fits |
| --- | --- | --- | --- |
| GitPython | `subprocess.run(["git", ...], capture_output=True, text=True)` | `src/utils.py` | Uses the system Git binary directly, no extra runtime package |
| Click | `argparse.ArgumentParser` + `add_subparsers()` | `src/cli.py` | Structured CLI parsing and subcommands (`analyze`, `stats`, `report`, `version`) |
| Rich | `print()` with fixed text blocks | `src/cli.py` | Plain, readable terminal output is enough for this CLI |
| Jinja2 | Python string formatting + `html.escape` | `src/html_report.py` | Renders the HTML report using f-strings and built-in escaping, no template engine |
| Pandas | `collections.Counter` / `dict` / sorted `list` comprehensions | `src/git_engine.py`, `src/summary.py`, `src/html_report.py` | Aggregation and counting (categories, hotspots, changed areas, contributors) is simple enough without a dataframe library |
| Flask | CLI-only architecture | `src/cli.py`, `src/main.py` | No web server is needed; the HTML report is a static file |
| pydantic | `dataclasses.dataclass(slots=True)` | `src/models.py` | Typed, memory-efficient models (`Commit`, `FileChange`, `DomainFinding`, `RiskAssessment`, `ExcludedFile`, `AnalysisResult`) without the dependency |
| pytest | `unittest.TestCase` + `unittest.main()` | `tests/` | Built-in testing framework for all unit and scenario tests |
| pathspec / gitignore-parser | `fnmatch.fnmatch` against normalized paths and path segments | `src/excludes.py` | Matches generated/build artifact patterns (`*.egg-info`, `build/`, `dist/`, `__pycache__`, etc.) without a gitignore-style parsing library |
| simplejson | `json.dumps(result.as_dict(), indent=2, ensure_ascii=False)` | `src/cli.py` | Machine-readable output behind the `--json` flag |
| `open`-in-browser helpers | `webbrowser.open(path.as_uri())` | `src/cli.py` | Opens the generated HTML report in the user's default browser behind `--open` |

## Notable substitutions

1. GitPython -> `subprocess.run([...], capture_output=True, text=True)` for every Git query (`log`, `diff-tree --name-status`, `diff-tree --numstat`, `rev-list --count`, `status`)
2. Click -> `argparse.ArgumentParser` and `add_subparsers()`
3. Rich -> `print()` with fixed text blocks
4. Jinja2 -> f-strings + `html.escape()` for the HTML report (`src/html_report.py`)
5. Pandas -> `collections.Counter`, plain `dict`, and sorted comprehensions
6. Flask -> command-line entry points and a static HTML file as output
7. pydantic -> `dataclasses.dataclass(slots=True)`
8. pytest -> `unittest.TestCase` and `unittest.main()`
9. pathspec -> `fnmatch.fnmatch` for generated/build artifact matching
10. simplejson -> `json` from the standard library
11. Structured Git parsing uses `\x1e`/`\x1f`/`\x00` (record/field/null) separators parsed with `str.split()` and `re`, instead of a Git-log-parsing library
12. Path tokenization for domain/category detection uses `re.split(r"[^a-z0-9]+", ...)` on lowercased, camelCase-split text instead of an NLP tokenizer

## Note on accuracy

This table is kept in sync with the actual imports in `src/`. If a
substitution is added or removed, this file is updated in the same change so
it never drifts from the implementation. Run `grep -rhn "^import \|^from " src/`
to check current imports against this table.
