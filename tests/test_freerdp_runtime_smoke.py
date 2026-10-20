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

    def assert_preflight_rejected(self, diagnostic):
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(diagnostic, result.stderr)
        self.assertNotIn("missing test tool", result.stderr)
        self.assertFalse(self.output.exists())

    def test_unlisted_dll_rejected(self):
        (self.runtime / "stale.DLL").write_bytes(b"not in manifest")
        self.assert_preflight_rejected("unlisted=['stale.DLL']")

    def test_unlisted_provider_rejected(self):
        providers = self.runtime / "ossl-modules"
        providers.mkdir()
        (providers / "extra.dll").write_bytes(b"not in manifest")
        self.assert_preflight_rejected("unlisted=['ossl-modules/extra.dll']")

    def test_symlinked_provider_directory_rejected(self):
        providers = self.root / "other-providers"
        providers.mkdir()
        (self.runtime / "ossl-modules").symlink_to(providers, target_is_directory=True)
        self.assert_preflight_rejected("provider directory must not be a symlink")

    def test_nested_symlinked_provider_directory_rejected(self):
        providers = self.runtime / "ossl-modules"
        providers.mkdir()
        (providers / "nested").symlink_to(self.root, target_is_directory=True)
        self.assert_preflight_rejected("provider directory must not be a symlink")

    def test_duplicate_manifest_entry_rejected(self):
        with (self.runtime / ".build-sha256").open("a") as stream:
            stream.write(f"{self.digest}  sdl-freerdp.exe\n")
        self.assert_preflight_rejected("unsafe or duplicate runtime checksum entry")

    def test_manifest_cannot_escape_runtime(self):
        with (self.runtime / ".build-sha256").open("a") as stream:
            stream.write(f"{self.digest}  ../outside.dll\n")
        self.assert_preflight_rejected("unsafe or duplicate runtime checksum entry")

    def test_manifest_cannot_name_unstaged_file(self):
        (self.runtime / "other.exe").write_bytes(b"not part of runtime")
        with (self.runtime / ".build-sha256").open("a") as stream:
            stream.write(f"{self.digest}  other.exe\n")
        self.assert_preflight_rejected("not staged=['other.exe']")

    def test_complete_inventory_reaches_tool_check(self):
        result = self.invoke()
        self.assertIn("missing test tool: /missing/wine-must-not-run", result.stderr)
        self.assertFalse(self.output.exists())

    def test_old_shim_is_excluded_from_runtime_input(self):
        # The helper compiles a new shim from the checked-out source.
        (self.runtime / "winpr-sspi-shim.dll").write_bytes(b"old generated shim")
        result = self.invoke()
        self.assertIn("missing test tool: /missing/wine-must-not-run", result.stderr)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
