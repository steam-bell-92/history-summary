import unittest

from src.parser import merge_file_changes, parse_git_log_output, parse_name_status_output, parse_numstat_output


LOG_OUTPUT = '''
1234567890abcdef\x1fAlice\x1f2026-08-01T12:00:00+00:00\x1ffeat(auth): add JWT validation\x1e
'''


class ParserTests(unittest.TestCase):
    def test_parse_git_log_output(self):
        commits = parse_git_log_output(LOG_OUTPUT)
        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0].author, "Alice")
        self.assertEqual(commits[0].message, "feat(auth): add JWT validation")

    def test_parse_structured_file_changes(self):
        name_status = "R100\0src/old name.py\0src/new name.py\0D\0docs/readme.md\0M\0assets/binary.bin\0"
        numstat = "0\t0\0src/old name.py\0src/new name.py\00\t1\tdocs/readme.md\0-\t-\tassets/binary.bin\0"

        merged = merge_file_changes(parse_name_status_output(name_status), parse_numstat_output(numstat))

        self.assertEqual(len(merged), 3)
        self.assertEqual(merged[0].old_path, "src/old name.py")
        self.assertEqual(merged[0].path, "src/new name.py")
        self.assertEqual(merged[1].status, "D")
        self.assertEqual(merged[1].deletions, 1)
        self.assertTrue(merged[2].is_binary)


if __name__ == "__main__":
    unittest.main()
