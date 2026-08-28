# Standard Library Replacements for Zero-Dependency Git Analysis

This project intentionally avoids third-party packages. Below are the standard library replacements for common patterns used in typical Python tooling.

| Common Dependency | Replacement in This Project | Why it fits |
| --- | --- | --- |
| GitPython | subprocess + git CLI | Uses the system Git binary directly without extra runtime packages |
| Click | argparse | Provides structured CLI parsing and subcommands |
| Rich | print + plain text formatting | Simple terminal output is enough for this CLI |
| Jinja2 | string formatting + html.escape | Renders HTML using Python's built-in string templates |
| Requests | subprocess + git | Git history and repository data is retrieved locally |
| Pandas | collections.Counter + dict/list | Aggregation and counts are simple and dependency-free |
| sqlite3 | optional JSON or in-memory collections | Local cache or temporary storage without external dependencies |
| colorama | ANSI escape code handling via print | Adds terminal style where necessary |
| watchdog | pathlib + os | Monitors filesystem paths without a library |
| Flask | CLI-only architecture | No web server is needed for this standalone project |
| pydantic | dataclasses | Type-safe models without the dependency |
| pytest | unittest | Built-in testing framework for core assertions |
| loguru | logging | Standard log support fits the project needs |
| toml | tomllib | Parses TOML configuration in Python 3.11+ |
| dateutil | datetime | Manages time parsing and formatting via stdlib |
| yaml | json + custom parsing | Git metadata and reports are simple enough for JSON/XML output |
| httpx | urllib | Local or remote HTTP needs can be handled with stdlib |
| numpy | statistics + collections | Basic statistics and counting can be implemented without numpy |

## Notable substitutions

1. GitPython -> subprocess.run([...], capture_output=True, text=True)
2. Click -> argparse.ArgumentParser and add_subparsers()
3. Rich -> print() with fixed text blocks
4. Jinja2 -> string.Template or format() with html.escape
5. Pandas -> Counter, defaultdict, and dictionary-based aggregation
6. Requests -> urllib.request for HTTP interactions (if needed)
7. Flask -> command-line entrypoints and static HTML output
8. PyYAML -> json.loads() / custom parsers for simple config
9. pydantic -> dataclasses.dataclass
10. pytest -> unittest.TestCase and unittest.main()
11. colorama -> ANSI sequences defined directly in code
12. watchfiles -> os.walk + pathlib.Path.rglob

This approach keeps the project portable, transparent, and compliant with the zero-dependency requirement.
