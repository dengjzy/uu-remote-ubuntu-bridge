"""Reject unpinned/mixed runtime inputs before starting Wine or a display."""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/test-freerdp-runtime.sh"


class FreeRDPRuntimePreflightTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir()
        client = self.runtime / "sdl-freerdp.exe"
        client.write_bytes(b"synthetic client, never executed")
        self.digest = hashlib.sha256(client.read_bytes()).hexdigest()
        (self.runtime / ".build-sha256").write_text(f"{self.digest}  sdl-freerdp.exe\n")
        self.output = self.root / "evidence"
        # Reaching dependency resolution or Wine would be a test failure.
        self.env = {**os.environ, "UURB_WINE_BIN": "/missing/wine-must-not-run"}

    def invoke(self, digest=None):
        return subprocess.run(
            ["bash", str(SCRIPT), str(self.runtime), digest or self.digest,
             "a" * 40, str(self.output)],
            capture_output=True, text=True, env=self.env, timeout=5,
        )

    def test_wrong_client_hash_rejected_before_runtime_creation(self):
        result = self.invoke("0" * 64)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAILED", result.stdout)
        self.assertNotIn("missing test tool", result.stderr)
        self.assertFalse(self.output.exists())

    def test_changed_dll_rejected_even_with_matching_client(self):
        library = self.runtime / "libwinpr3.dll"
        library.write_bytes(b"changed runtime")
        with (self.runtime / ".build-sha256").open("a") as stream:
            stream.write("0" * 64 + "  libwinpr3.dll\n")
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("libwinpr3.dll: FAILED", result.stdout)
        self.assertNotIn("missing test tool", result.stderr)
        self.assertFalse(self.output.exists())

    def test_existing_evidence_is_preserved(self):
        self.output.mkdir()
        sentinel = self.output / "keep.txt"
        sentinel.write_text("previous evidence")
        result = self.invoke()
        self.assertEqual(result.returncode, 2)
        self.assertIn("never overwritten", result.stderr)
        self.assertEqual(sentinel.read_text(), "previous evidence")


if __name__ == "__main__":
    unittest.main()
