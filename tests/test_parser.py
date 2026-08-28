import unittest

from src.parser import parse_git_log_output


LOG_OUTPUT = '''
commit 1234567890abcdef
Author: Alice <alice@example.com>
Date:   2026-08-01 12:00:00 +0000

    feat(auth): add JWT validation

    src/auth.py | 12 ++++++
    src/api.py  | 4 +--
    2 files changed, 12 insertions(+), 4 deletions(-)

'''


class ParserTests(unittest.TestCase):
    def test_parse_git_log_output(self):
        commits = parse_git_log_output(LOG_OUTPUT)
        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0].author, "Alice")
        self.assertEqual(commits[0].message, "feat(auth): add JWT validation")
        self.assertEqual(commits[0].files_changed, 2)
        self.assertEqual(commits[0].insertions, 12)
        self.assertEqual(commits[0].deletions, 4)


if __name__ == "__main__":
    unittest.main()
