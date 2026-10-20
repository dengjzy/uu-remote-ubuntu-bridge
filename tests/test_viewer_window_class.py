"""The UU viewer window must not share the system TigerVNC launcher's class.

Runs the real `uu-remote-console window` against a private Xvfb, x11vnc and
TigerVNC viewer with a stand-in UU window. Skips without those tools.
"""

import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

CONSOLE = Path(__file__).resolve().parents[1] / "scripts" / "uu-remote-console"
TOOLS = ("Xvfb", "openbox", "x11vnc", "xdotool", "xdpyinfo", "xprop")
VIEWER = os.environ.get("UURB_TEST_TIGERVNC", "/usr/bin/vncviewer")


def fixture_available():
    if any(shutil.which(tool) is None for tool in TOOLS):
        return False
    try:
        viewer = subprocess.run([VIEWER, "-help"], capture_output=True,
                                text=True, timeout=5)
        gtk = subprocess.run([sys.executable, "-c",
            'import gi; gi.require_version("Gtk", "3.0"); from gi.repository import Gtk'],
            capture_output=True, timeout=5)
        return "TigerVNC" in viewer.stdout + viewer.stderr and not gtk.returncode
    except (OSError, subprocess.TimeoutExpired):
        return False


FIXTURE_AVAILABLE = fixture_available()
if os.environ.get("UURB_REQUIRE_VIEWER_TESTS") == "1" and not FIXTURE_AVAILABLE:
    raise RuntimeError("Required viewer test dependencies are unavailable")


FAKE_UU = """
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
window = Gtk.Window()
window.set_wmclass("gameviewer.exe", "gameviewer.exe")
window.set_title("UU")
window.set_default_size(600, 400)
window.show_all()
Gtk.main()
"""


@unittest.skipUnless(FIXTURE_AVAILABLE,
                    "needs Xvfb, openbox, x11vnc, TigerVNC, xdotool and GTK 3")
class ViewerWindowClassTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.root = root
        # Allow a privately extracted TigerVNC package without replacing the
        # host's RealVNC binary. The actual console code is otherwise unchanged.
        self.console = root / "uu-remote-console"
        self.console.write_text(CONSOLE.read_text().replace("/usr/bin/vncviewer", VIEWER))
        authority = root / "run" / "uu-remote-bridge" / "Xauthority"
        authority.parent.mkdir(parents=True)
        authority.touch()
        number = next(n for n in range(90, 200)
                      if not Path(f"/tmp/.X11-unix/X{n}").exists())
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        self.env = {
            **os.environ, "HOME": str(root), "XDG_RUNTIME_DIR": str(root / "run"),
            "XDG_STATE_HOME": str(root / "state"), "DISPLAY": f":{number}",
            "XAUTHORITY": str(authority), "UURB_CONSOLE_VNC_PORT": str(port),
            "GDK_BACKEND": "x11",
        }
        self.children = []
        self.addCleanup(self.stop_children)
        display = self.spawn(["Xvfb", f":{number}", "-screen", "0", "1280x800x24",
                    "-nolisten", "tcp", "-auth", str(authority)])
        deadline = time.monotonic() + 10
        while not Path(f"/tmp/.X11-unix/X{number}").exists():
            self.assertIsNone(display.poll(), "fixture Xvfb exited")
            self.assertLess(time.monotonic(), deadline, "fixture Xvfb did not start")
            time.sleep(0.1)
        (root / "run/uu-remote-bridge/private-display").write_text(f":{number}\n")
        self.spawn(["openbox"])
        self.spawn([sys.executable, "-c", FAKE_UU])

    def spawn(self, argv):
        with (self.root / "fixture.log").open("ab") as log:
            process = subprocess.Popen(argv, env=self.env, start_new_session=True,
                                       stdout=log, stderr=log)
        self.children.append(process)
        return process

    def stop_children(self):
        for process in reversed(self.children):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)

    def viewer_windows(self, window_class):
        found = subprocess.run(["xdotool", "search", "--class", window_class],
                               env=self.env, capture_output=True, text=True).stdout
        return [w for w in found.split() if "UU Remote - TigerVNC" in subprocess.run(
            ["xdotool", "getwindowname", w], env=self.env,
            capture_output=True, text=True).stdout]

    def test_viewer_gets_its_own_class_and_reopening_reuses_it(self):
        opened = self.spawn(["bash", str(self.console), "window"])
        deadline = time.time() + 30
        while not (found := self.viewer_windows("^UU-Remote$")):
            self.assertIsNone(opened.poll(), self.diagnostics())
            self.assertLess(time.time(), deadline, self.diagnostics())
            time.sleep(0.2)
        self.assertEqual([], self.viewer_windows("^TigerVNC Viewer$"))

        again = subprocess.run(["bash", str(self.console), "window"], env=self.env,
                               capture_output=True, text=True, timeout=30)
        self.assertEqual(0, again.returncode, again.stderr)
        self.assertEqual(found, self.viewer_windows("^UU-Remote$"))
        self.assertIsNone(opened.poll())

    def diagnostics(self):
        return "\n".join(p.read_text(errors="replace")[-3000:]
                         for p in self.root.rglob("*.log"))

    def test_close_releases_lock_even_if_exporter_is_stopped(self):
        opened = self.spawn(["bash", str(self.console), "window"])
        deadline = time.monotonic() + 20
        while not self.viewer_windows("^UU-Remote$"):
            self.assertIsNone(opened.poll(), self.diagnostics())
            self.assertLess(time.monotonic(), deadline, self.diagnostics())
            time.sleep(.1)
        # Only signal the exporter created by this fixture's console process.
        child_ids = Path(f"/proc/{opened.pid}/task/{opened.pid}/children").read_text().split()
        exporters = [int(pid) for pid in child_ids
                     if Path(f"/proc/{pid}/comm").read_text().strip() == "x11vnc"]
        self.assertEqual(len(exporters), 1)
        os.kill(exporters[0], signal.SIGSTOP)
        result = subprocess.run(["bash", str(self.console), "close"], env=self.env,
                                capture_output=True, text=True, timeout=12)
        self.assertEqual(result.returncode, 0, result.stderr)
        opened.wait(timeout=3)
        self.assertFalse(Path(f"/proc/{exporters[0]}").exists())
        self.assertEqual([], self.viewer_windows("^UU-Remote$"))
        lock = self.root / "run/uu-remote-console/window.lock"
        result = subprocess.run(["flock", "-n", str(lock), "true"], timeout=3)
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
