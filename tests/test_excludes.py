import unittest

from src.excludes import DEFAULT_EXCLUDE_PATTERNS, is_generated_artifact, matched_exclude_pattern, resolve_patterns


class ExcludesTests(unittest.TestCase):
    def test_egg_info_directory_is_detected(self):
        self.assertTrue(is_generated_artifact("gitlens_zero.egg-info/PKG-INFO"))

    def test_build_directory_at_any_depth_is_detected(self):
        self.assertTrue(is_generated_artifact("src/pkg/build/output.txt"))

    def test_dist_directory_is_detected(self):
        self.assertTrue(is_generated_artifact("dist/gitlens_zero-0.1.0.tar.gz"))

    def test_pycache_directory_is_detected(self):
        self.assertTrue(is_generated_artifact("src/__pycache__/cli.cpython-312.pyc"))

    def test_normal_source_file_is_not_excluded(self):
        self.assertFalse(is_generated_artifact("src/cli.py"))

    def test_file_named_like_a_pattern_but_not_matching_segment_is_not_excluded(self):
        # "rebuild.py" contains "build" as a substring but not as a path segment/pattern match.
        self.assertFalse(is_generated_artifact("src/rebuild.py"))

    def test_matched_pattern_is_reported(self):
        pattern = matched_exclude_pattern("dist/output.whl")
        self.assertIn(pattern, DEFAULT_EXCLUDE_PATTERNS)

    def test_no_patterns_means_nothing_is_excluded(self):
        self.assertIsNone(matched_exclude_pattern("build/output.txt", patterns=()))

    def test_resolve_patterns_include_generated_disables_everything(self):
        patterns = resolve_patterns(["*.custom"], include_generated=True)
        self.assertEqual(patterns, ())

    def test_resolve_patterns_adds_custom_pattern_to_defaults(self):
        patterns = resolve_patterns(["*.custom"], include_generated=False)
        self.assertIn("*.custom", patterns)
        for default_pattern in DEFAULT_EXCLUDE_PATTERNS:
            self.assertIn(default_pattern, patterns)

    def test_custom_pattern_is_applied(self):
        patterns = resolve_patterns(["*.generated.json"], include_generated=False)
        self.assertTrue(is_generated_artifact("data/schema.generated.json", patterns))


if __name__ == "__main__":
    unittest.main()
