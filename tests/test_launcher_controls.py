"""Launcher quit and start-at-login controls, run against stub commands.

Nothing here touches a real systemd user manager or desktop session:
systemctl and notify-send are stubs that log their arguments, and the launcher
under test is a copy that calls the stub.
"""

import configparser
import json
import os
import shlex
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPERS = ROOT / "scripts" / "launcher-install.sh"
INSTALLER = ROOT / "install.sh"
SERVICE = "uu-remote-bridge.service"

SYSTEMCTL_STUB = """#!/bin/bash
printf 'systemctl %s\\n' "$*" >>"$STUB_LOG"
verb="$2"
[[ "$verb" == "${STUB_FAIL_VERB:-}" ]] && exit 5
case "$verb" in
    show)
        if [[ -z "${STUB_ENABLED:-}" ]]; then
            printf 'LoadState=not-found\\nUnitFileState=\\n'
        else
            printf 'LoadState=%s\\nUnitFileState=%s\\n' "${STUB_LOAD_STATE:-loaded}" "$STUB_ENABLED"
        fi
        exit 0
        ;;
    is-enabled)
        if [[ -n "${STUB_ENABLED:-}" ]]; then
            printf '%s\\n' "$STUB_ENABLED"
            [[ "$STUB_ENABLED" == enabled ]]
            exit
        fi
        printf 'Failed to get unit file state: No such file\\n' >&2
        exit 1
        ;;
    is-active)
        printf '%s\\n' "${STUB_ACTIVE:-inactive}"
        exit 0
        ;;
esac
exit 0
"""
NOTIFY_STUB = """#!/bin/bash
printf 'notify %s\\n' "$*" >>"$STUB_LOG"
"""


class Sandbox:
    """A private home, stub commands and a launcher copy that uses them."""

    def __init__(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.home = root / "home"
        self.home.mkdir()
        self.bin = root / "bin"
        self.bin.mkdir()
        self.log = root / "calls.log"
        self.log.touch()
        # The launcher lives in a directory with a space, like a home folder
        # that has one, so the rendered Exec= lines are exercised too.
        self.executable = root / "with space" / "uu-remote"
        self.executable.parent.mkdir()
        self.systemctl = self.stub("systemctl", SYSTEMCTL_STUB)
        self.stub("notify-send", NOTIFY_STUB)
        for name in ("bash", "mkdir"):
            (self.bin / name).symlink_to(shutil.which(name))
        text = (ROOT / "scripts" / "uu-remote").read_text()
        # The launcher hard-codes the absolute systemctl path on purpose.
        assert text.count("/usr/bin/systemctl") == 1
        self.executable.write_text(
            text.replace("/usr/bin/systemctl", str(self.systemctl))
        )
        self.executable.chmod(0o700)

    def stub(self, name, body):
        path = self.bin / name
        path.write_text(body)
        path.chmod(0o700)
        return path

    def environment(self, **extra):
        return {
            "HOME": str(self.home),
            "XDG_STATE_HOME": str(self.home / "state"),
            "XDG_RUNTIME_DIR": str(self.home / "run"),
            "PATH": str(self.bin),
            "DISPLAY": ":99",
            "STUB_LOG": str(self.log),
            **extra,
        }

    def run(self, argv, **extra):
        return subprocess.run(
            argv,
            env=self.environment(**extra),
            capture_output=True,
            text=True,
            timeout=30,
        )

    def launcher(self, *args, **extra):
        return self.run(["/usr/bin/bash", str(self.executable), *args], **extra)

    def calls(self):
        return self.log.read_text().splitlines()

    def cleanup(self):
        self.directory.cleanup()


class LauncherCommandTests(unittest.TestCase):
    def sandbox(self):
        box = Sandbox()
        self.addCleanup(box.cleanup)
        return box

    def test_stop_stops_the_service_and_tells_the_user(self):
        box = self.sandbox()
        result = box.launcher("stop")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("quit completely", result.stdout)
        calls = box.calls()
        self.assertIn(f"systemctl --user stop {SERVICE}", calls)
        self.assertTrue(any(call.startswith("notify") for call in calls))

    def test_stop_failure_is_reported_not_hidden(self):
        box = self.sandbox()
        result = box.launcher("stop", STUB_FAIL_VERB="stop")
        self.assertEqual(result.returncode, 5)
        self.assertNotIn("quit completely", result.stdout)
        self.assertFalse(any(c.startswith("notify") for c in box.calls()))

    def test_autostart_on_and_off_enable_and_disable_the_service(self):
        for action, verb in (("on", "enable"), ("off", "disable")):
            with self.subTest(action=action):
                box = self.sandbox()
                result = box.launcher("autostart", action)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    [f"systemctl --user {verb} {SERVICE}"],
                    [c for c in box.calls() if not c.startswith("notify")],
                )
                self.assertTrue(result.stdout.strip())

    def test_autostart_failure_is_propagated_without_a_success_message(self):
        for action, verb in (("on", "enable"), ("off", "disable")):
            with self.subTest(action=action):
                box = self.sandbox()
                result = box.launcher("autostart", action, STUB_FAIL_VERB=verb)
                self.assertEqual(result.returncode, 5)
                self.assertEqual("", result.stdout)
                self.assertFalse(any(c.startswith("notify") for c in box.calls()))

    def test_autostart_status_prints_the_unit_state(self):
        for state in ("enabled", "disabled"):
            with self.subTest(state=state):
                box = self.sandbox()
                result = box.launcher("autostart", STUB_ENABLED=state)
                self.assertEqual(result.returncode, 0 if state == "enabled" else 1, result.stderr)
                self.assertEqual(state, result.stdout.strip())
                result = box.launcher("autostart", "status", STUB_ENABLED=state)
                self.assertEqual(state, result.stdout.strip())

    def test_status_does_not_hide_manager_failure(self):
        box = self.sandbox()
        result = box.launcher("autostart", "status", STUB_FAIL_VERB="is-enabled")
        self.assertEqual(5, result.returncode)

    def test_autostart_rejects_an_unknown_action(self):
        box = self.sandbox()
        result = box.launcher("autostart", "maybe")
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage: uu-remote autostart", result.stderr)
        self.assertEqual([], box.calls())



class RenderedLauncherTests(unittest.TestCase):
    """The installed .desktop file, as install.sh renders it."""

    def render(self, destination, executable):
        subprocess.run(
            [
                "bash", "-c",
                'source "$1"; shift; python_bin=/usr/bin/python3; render_desktop_entry "$@"',
                "test", str(HELPERS),
                str(ROOT / "desktop" / "uu-remote.desktop.in"), str(destination), str(executable),
            ],
            check=True,
            capture_output=True,
        )
        parser = configparser.ConfigParser(interpolation=None, delimiters=("=",))
        parser.optionxform = str
        parser.read(destination, encoding="utf-8")
        return parser

    def test_right_click_actions_run_the_launcher_with_the_intended_subcommands(self):
        box = Sandbox()
        self.addCleanup(box.cleanup)
        entry = self.render(Path(box.directory.name) / "main.desktop", box.executable)
        exe = str(box.executable)

        def argv(section):
            return shlex.split(entry[section]["Exec"])

        # Opening starts Wine, so it is only checked, not run.
        prefix = ["/usr/bin/env", "--", exe]
        self.assertEqual(prefix + ["open"], argv("Desktop Entry"))
        self.assertEqual("Quit;AutostartOn;AutostartOff;", entry["Desktop Entry"]["Actions"])
        actions = {
            "Desktop Action Quit": (prefix + ["stop"], "stop"),
            "Desktop Action AutostartOn": (prefix + ["autostart", "on"], "enable"),
            "Desktop Action AutostartOff": (prefix + ["autostart", "off"], "disable"),
        }
        for section, (expected, verb) in actions.items():
            with self.subTest(section=section):
                self.assertEqual(expected, argv(section))
                box.log.write_text("")
                result = box.run(argv(section))
                self.assertEqual(result.returncode, 0, result.stderr)
                changes = [c for c in box.calls() if c.startswith("systemctl")]
                self.assertEqual([f"systemctl --user {verb} {SERVICE}"], changes)

    @unittest.skipUnless(shutil.which("desktop-file-validate"), "no validator")
    def test_rendered_entry_is_a_valid_desktop_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "uu-remote.desktop"
            self.render(destination, "/opt/uu/bin/uu-remote")
            result = subprocess.run(["desktop-file-validate", str(destination)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("gio"), "needs GLib's actual desktop launcher")
    def test_gio_launches_literal_executable_paths_not_shell_escape_lookalikes(self):
        # shlex.split() is not a desktop-entry parser: the old backslash-space
        # form passed it and desktop-file-validate, but GIO discarded Exec.
        for folder in ["with space", '引号 " dollar $ backtick ` percent %f slash \\']:
            with self.subTest(folder=folder), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                executable = root / folder / "harmless-launcher"
                executable.parent.mkdir()
                marker = root / "args.json"
                executable.write_text(
                    '#!/usr/bin/python3\nimport sys,json\nfrom pathlib import Path\n'
                    f'Path({str(marker)!r}).write_text(json.dumps(sys.argv[1:]))\n'
                )
                executable.chmod(0o700)
                entry = root / "uu-remote.desktop"
                self.render(entry, executable)
                env = dict(os.environ, HOME=str(root), XDG_RUNTIME_DIR=str(root),
                           DBUS_SESSION_BUS_ADDRESS="unix:path=" + str(root / "no-bus"))
                result = subprocess.run(["gio", "launch", str(entry)], env=env,
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(0, result.returncode, result.stderr)
                deadline = time.monotonic() + 5
                while not marker.exists() and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertTrue(marker.exists(), "literal executable was not launched")
                self.assertEqual(["open"], json.loads(marker.read_text()))


class InstallerAutostartTests(unittest.TestCase):
    """install.sh keeps an earlier `autostart off`."""

    def installer_step(self, enabled, **extra):
        # Same order as install.sh: read the state, write the unit, refresh.
        box = Sandbox()
        self.addCleanup(box.cleanup)
        script = (
            'set -Eeuo pipefail; source "$1"; shift; '
            'prior="$(bridge_autostart_state "$@")"; '
            'printf "prior=%s\\n" "$prior"; '
            'refresh_bridge_autostart "$prior" "$@"'
        )
        result = box.run(
            ["/usr/bin/bash", "-c", script, "test", str(HELPERS), str(box.systemctl),
             "--user"],
            STUB_ENABLED=enabled,
            **extra,
        )
        reenabled = f"systemctl --user reenable {SERVICE}" in box.calls()
        return result, reenabled

    def test_new_install_starts_at_login(self):
        result, reenabled = self.installer_step("")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("prior=not-found\n", result.stdout)
        self.assertTrue(reenabled)

    def test_reinstall_keeps_an_enabled_service_enabled(self):
        result, reenabled = self.installer_step("enabled")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(reenabled)

    def test_reinstall_keeps_autostart_off_and_says_how_to_turn_it_on(self):
        result, reenabled = self.installer_step("disabled")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(reenabled)
        self.assertIn("stays off", result.stdout)
        self.assertIn("uu-remote autostart on", result.stdout)

    def test_a_failing_systemctl_aborts_the_install_step(self):
        for enabled in ("", "enabled"):
            with self.subTest(prior=enabled or "new install"):
                result, reenabled = self.installer_step(
                    enabled, STUB_FAIL_VERB="reenable"
                )
                self.assertEqual(result.returncode, 5)
                self.assertTrue(reenabled)

    def test_query_failure_does_not_reenable_the_service(self):
        result, reenabled = self.installer_step("disabled", STUB_FAIL_VERB="show")
        self.assertEqual(5, result.returncode)
        self.assertFalse(reenabled)

    def test_masked_or_unrecognized_states_abort_without_reenable(self):
        for state, load in [("masked", "masked"), ("linked", "loaded"),
                            ("unexpected", "loaded"), ("enabled", "error")]:
            with self.subTest(state=state, load=load):
                result, reenabled = self.installer_step(state, STUB_LOAD_STATE=load)
                self.assertNotEqual(0, result.returncode)
                self.assertFalse(reenabled)
                self.assertIn("Cannot safely preserve", result.stderr)

    def test_runtime_only_enablement_stays_runtime_only(self):
        result, _ = self.installer_step("enabled-runtime")
        self.assertEqual(0, result.returncode, result.stderr)
        # Also inspect the exact verb; do not turn a temporary choice permanent.
        box = Sandbox()
        self.addCleanup(box.cleanup)
        result = box.run(["bash", "-c", 'source "$1"; refresh_bridge_autostart enabled-runtime "$2" --user',
                          "test", str(HELPERS), str(box.systemctl)])
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(f"systemctl --user reenable --runtime {SERVICE}", box.calls())

    def test_the_state_is_read_before_the_unit_file_is_written(self):
        source = INSTALLER.read_text()
        read = source.index('prior_autostart="$(bridge_autostart_state')
        write = source.index(
            'install -m 0644 "$repo_dir/systemd/uu-remote-bridge.service"'
        )
        refresh = source.index('refresh_bridge_autostart "$prior_autostart"')
        self.assertLess(read, write)
        self.assertLess(read, source.index('"${systemctl_user[@]}" stop uu-remote-bridge.service'))
        self.assertLess(write, refresh)
        self.assertNotIn(f"reenable {SERVICE}", source)


if __name__ == "__main__":
    unittest.main()
