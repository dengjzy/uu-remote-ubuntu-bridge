"""Exercise console focus helpers with fake X commands, never a live desktop."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SOURCE = (Path(__file__).resolve().parents[1] / "scripts/uu-remote-console").read_text()


class ConsoleFocusTests(unittest.TestCase):
    def run_helpers(self, mode, commands):
        with tempfile.TemporaryDirectory(prefix="uu-focus-test-") as temp:
            directory = Path(temp)
            xdo = directory / "xdotool"
            xdo.write_text('''#!/usr/bin/env bash
case "$*" in
  *search*gameviewer*) printf '100\\n200\\n';;
  *getwindowname*) printf 'UU Remote\\n';;
  *search*Ubuntu-Desktop-Relay*)
    [[ "$FOCUS_TEST_MODE" == rdp ]] || exit 1
    printf '101\\n';;
  *search*realvnc-vncviewer*)
    [[ "$FOCUS_TEST_MODE" == vnc ]] || exit 1
    printf '202\\n';;
  *) printf '%s\\n' "$*" >> "$FOCUS_TEST_LOG";;
esac
''')
            xprop = directory / "xprop"
            xprop.write_text('''#!/usr/bin/env bash
if [[ "$*" == *100* ]]; then
    printf 'WM_STATE(WM_STATE): window state: Normal\\n'
else
    printf 'WM_STATE: not found.\\n'
fi
''')
            xdo.chmod(0o700)
            xprop.chmod(0o700)
            # Source only definitions, substitute private fake X executables,
            # and override discovery so the real X server is never used.
            script = SOURCE.split('case "${1:-open}" in', 1)[0]
            script = script.replace("/usr/bin/xdotool", str(xdo)).replace("/usr/bin/xprop", str(xprop))
            script += '\ndiscover_bridge() { bridge_display=:99; bridge_xauthority=/none; }\n'
            script += commands
            env = dict(os.environ, HOME=temp, XDG_RUNTIME_DIR=temp, XDG_STATE_HOME=temp,
                       FOCUS_TEST_MODE=mode, FOCUS_TEST_LOG=str(directory / "calls"))
            result = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True)
            calls = (directory / "calls").read_text() if (directory / "calls").exists() else ""
            return result, calls, (directory / "uu-remote-bridge/console-focus").exists()

    def test_restores_rdp(self):
        result, calls, lease = self.run_helpers("rdp", "focus_client; release_client")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("windowactivate 101", calls)
        self.assertFalse(lease)

    def test_restores_native_vnc_and_filters_toast(self):
        result, calls, lease = self.run_helpers("vnc", "focus_client; release_client")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("windowmap 100 windowactivate --sync 100", calls)
        self.assertNotIn("200", calls)
        self.assertIn("windowactivate 202", calls)
        self.assertFalse(lease)

    def test_missing_relay_still_releases_lease(self):
        result, calls, lease = self.run_helpers("none", "focus_client; release_client")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("windowactivate 101", calls)
        self.assertNotIn("windowactivate 202", calls)
        self.assertFalse(lease)


class ConsoleBridgeReuseTests(unittest.TestCase):
    """Login must reuse a live bridge, and only start an absent one."""

    def ensure(self, discovered, process_alive, start_status=0, wait_status=0):
        with tempfile.TemporaryDirectory(prefix='uu-console-start-test-') as temp:
            path = Path(temp)
            pgrep = path / 'pgrep'
            pgrep.write_text(f'#!/bin/sh\nexit {0 if process_alive else 1}\n')
            pgrep.chmod(0o700)
            script = SOURCE.split('case "${1:-open}" in', 1)[0]
            script = script.replace('/usr/bin/pgrep', str(pgrep))
            script += f'''
discover_bridge() {{ return {0 if discovered else 1}; }}
manager() {{ printf 'manager %s\\n' "$*"; return {start_status}; }}
wait_for_bridge() {{ printf 'wait\\n'; return {wait_status}; }}
systemctl_user=(manager)
ensure_bridge
'''
            return subprocess.run(['bash', '-c', script],
                                  env=dict(os.environ, HOME=temp, XDG_RUNTIME_DIR=temp,
                                           XDG_STATE_HOME=temp),
                                  capture_output=True, text=True, timeout=10)

    def test_live_bridge_is_reused_without_any_service_action(self):
        result = self.ensure(True, True)
        self.assertEqual((0, ''), (result.returncode, result.stdout), result.stderr)

    def test_starting_bridge_is_waited_for_without_duplicate_start(self):
        result = self.ensure(False, True)
        self.assertEqual((0, 'wait\n'), (result.returncode, result.stdout), result.stderr)

    def test_absent_bridge_is_started_once_and_waited_for(self):
        result = self.ensure(False, False)
        self.assertEqual((0, 'manager start uu-remote-bridge.service\nwait\n'),
                         (result.returncode, result.stdout), result.stderr)

    def test_start_and_readiness_failures_are_returned(self):
        result = self.ensure(False, False, start_status=7)
        self.assertEqual((1, 'manager start uu-remote-bridge.service\n'),
                         (result.returncode, result.stdout), result.stderr)
        result = self.ensure(False, True, wait_status=8)
        self.assertEqual((8, 'wait\n'), (result.returncode, result.stdout), result.stderr)


class ConsoleCaptureCommandTests(unittest.TestCase):
    def test_window_capture_does_not_silently_become_root_capture(self):
        # Record the executed argv, not a substring that can also occur in a
        # comment. This guards the capture default, not X11 input isolation.
        with tempfile.TemporaryDirectory(prefix='uu-console-argv-test-') as temp:
            path = Path(temp)
            server = path / 'x11vnc'
            server.write_text('''#!/bin/sh
printf '%s\\0' "$@" >"$HOME/capture-argv"
exec /bin/sleep 30
''')
            viewer = path / 'vncviewer'
            viewer.write_text('''#!/bin/sh
for i in $(seq 1 100); do
    test -f "$HOME/capture-argv" && exit 0
    sleep 0.01
done
exit 1
''')
            harmless = path / 'dependency'
            harmless.write_text('#!/bin/sh\nexit 0\n')
            for stub in (server, viewer, harmless):
                stub.chmod(0o700)
            script = SOURCE.split('case "${1:-open}" in', 1)[0]
            script = script.replace('/usr/bin/x11vnc', str(server))
            script = script.replace('/usr/bin/vncviewer', str(viewer))
            for dependency in ('ss', 'xdotool', 'xdpyinfo'):
                script = script.replace('/usr/bin/' + dependency, str(harmless))
            script += '''
ensure_bridge() { bridge_display=:99; bridge_xauthority=/unused; }
find_client_window() { printf '123\\n'; }
choose_window_port() { printf '55123\\n'; }
listener_present() { return 0; }
focus_client() { :; }
release_client() { :; }
open_window
'''
            result = subprocess.run(['bash', '-c', script],
                                    env=dict(os.environ, HOME=temp, DISPLAY=':99',
                                             XDG_RUNTIME_DIR=temp, XDG_STATE_HOME=temp),
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(0, result.returncode, result.stderr)
            args = (path / 'capture-argv').read_bytes().split(b'\x00')[:-1]
            self.assertIn(b'-id', args)
            self.assertEqual(b'123', args[args.index(b'-id') + 1])
            self.assertFalse({b'-sid', b'-clip', b'-rawfb'} & set(args))


if __name__ == "__main__":
    unittest.main()
