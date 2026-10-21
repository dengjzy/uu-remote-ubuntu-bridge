"""Keep imported source notices byte-exact and their origins reproducible."""
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
NOTICES = ROOT / "docs/dependencies/freerdp-2101-licenses"


class DependencyNoticeIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.entries = json.loads((NOTICES / "sources.json").read_text())["entries"]

    def test_original_notice_bytes_match_recorded_hashes(self):
        names = [entry["file"] for entry in self.entries]
        self.assertTrue(names)
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(names), {p.name for p in NOTICES.iterdir()
                                      if p.name != "sources.json"})
        for entry in self.entries:
            with self.subTest(file=entry["file"]):
                self.assertEqual(Path(entry["file"]).name, entry["file"])
                self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
                path = NOTICES / entry["file"]
                self.assertFalse(path.is_symlink())
                data = path.read_bytes()
                self.assertTrue(data)
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])

    def test_sources_use_immutable_revisions_and_distinguish_reference_versions(self):
        for entry in self.entries:
            with self.subTest(file=entry["file"]):
                self.assertRegex(entry["source_revision"], r"^[0-9a-f]{40}$")
                self.assertTrue(re.fullmatch(r"[\w.-]+/[\w.-]+", entry["source_repository"]))
                self.assertEqual(entry["source_url"],
                    f"https://raw.githubusercontent.com/{entry['source_repository']}/"
                    f"{entry['source_revision']}/{entry['source_path']}")
                self.assertIn(entry["identity_scope"], {
                    "version-or-source-correlated", "reference-only-version-not-established"})


if __name__ == "__main__":
    unittest.main()
