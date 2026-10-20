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
TOOLS = ("Xvfb", "openbox", "x11vnc", "vncviewer", "xdotool", "xdpyinfo", "xprop")
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


@unittest.skipIf(
    any(shutil.which(tool) is None for tool in TOOLS)
    or subprocess.run([sys.executable, "-c", "import gi"]).returncode,
    "needs Xvfb, openbox, x11vnc, vncviewer, xdotool and python3-gi",
)
class ViewerWindowClassTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
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
        self.spawn(["Xvfb", f":{number}", "-screen", "0", "1280x800x24",
                    "-nolisten", "tcp", "-auth", str(authority)])
        while not Path(f"/tmp/.X11-unix/X{number}").exists():
            time.sleep(0.1)
        self.spawn(["openbox"])
        self.spawn([sys.executable, "-c", FAKE_UU])

    def spawn(self, argv):
        process = subprocess.Popen(argv, env=self.env, start_new_session=True,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.children.append(process)
        return process

    def stop_children(self):
        for process in reversed(self.children):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()

    def viewer_windows(self, window_class):
        found = subprocess.run(["xdotool", "search", "--class", window_class],
                               env=self.env, capture_output=True, text=True).stdout
        return [w for w in found.split() if "UU Remote - TigerVNC" in subprocess.run(
            ["xdotool", "getwindowname", w], env=self.env,
            capture_output=True, text=True).stdout]

    def test_viewer_gets_its_own_class_and_reopening_reuses_it(self):
        opened = self.spawn(["bash", str(CONSOLE), "window"])
        deadline = time.time() + 30
        while not (found := self.viewer_windows("^UU-Remote$")):
            self.assertLess(time.time(), deadline, "viewer never got the UU-Remote class")
            time.sleep(0.2)
        self.assertEqual([], self.viewer_windows("^TigerVNC Viewer$"))

        again = subprocess.run(["bash", str(CONSOLE), "window"], env=self.env,
                               capture_output=True, text=True, timeout=30)
        self.assertEqual(0, again.returncode, again.stderr)
        self.assertEqual(found, self.viewer_windows("^UU-Remote$"))
        self.assertIsNone(opened.poll())


if __name__ == "__main__":
    unittest.main()
