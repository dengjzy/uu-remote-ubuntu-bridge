"""Launcher quit and start-at-login controls, run against stub commands.

Nothing here touches a real systemd user manager, desktop session or package
database: systemctl, zenity, notify-send and sudo are stubs that log their
arguments, and the launcher under test is a copy that calls the stub.
"""

import configparser
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPERS = ROOT / "scripts" / "launcher-install.sh"
INSTALLER = ROOT / "install.sh"
SERVICE = "uu-remote-bridge.service"

SYSTEMCTL_STUB = """#!/bin/bash
printf 'systemctl %s\\n' "$*" >>"$STUB_LOG"
verb="$2"
case "$verb" in
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
[[ "$verb" == "${STUB_FAIL_VERB:-}" ]] && exit 5
exit 0
"""
NOTIFY_STUB = """#!/bin/bash
printf 'notify %s\\n' "$*" >>"$STUB_LOG"
"""
ZENITY_STUB = """#!/bin/bash
printf 'zenity\\n' >>"$STUB_LOG"
printf '%s\\n' "${STUB_CHOICE:-}"
exit "${STUB_ZENITY_RC:-0}"
"""


class Sandbox:
    """A private home, stub commands and a launcher copy that uses them."""

    def __init__(self, *, zenity=True):
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
        if zenity:
            self.stub("zenity", ZENITY_STUB)
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
    def sandbox(self, **options):
        box = Sandbox(**options)
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
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(state, result.stdout.strip())
                result = box.launcher("autostart", "status", STUB_ENABLED=state)
                self.assertEqual(state, result.stdout.strip())

    def test_autostart_rejects_an_unknown_action(self):
        box = self.sandbox()
        result = box.launcher("autostart", "maybe")
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage: uu-remote autostart", result.stderr)
        self.assertEqual([], box.calls())

    def test_settings_dialog_without_zenity_explains_and_changes_nothing(self):
        # What a --skip-packages install on a host without zenity looks like.
        box = self.sandbox(zenity=False)
        result = box.launcher("manage")
        self.assertEqual(result.returncode, 1)
        self.assertIn("needs zenity", result.stderr)
        self.assertIn("uu-remote stop", result.stderr)
        self.assertEqual(
            [], [c for c in box.calls() if c.startswith("systemctl")]
        )

    def test_settings_dialog_runs_the_chosen_action_only(self):
        expected = {
            "quit": "stop",
            "on": "enable",
            "off": "disable",
        }
        for choice, verb in expected.items():
            with self.subTest(choice=choice):
                box = self.sandbox()
                result = box.launcher("manage", STUB_CHOICE=choice)
                self.assertEqual(result.returncode, 0, result.stderr)
                changes = [
                    c for c in box.calls()
                    if c.startswith("systemctl")
                    and c.split()[2] not in ("is-active", "is-enabled")
                ]
                self.assertEqual([f"systemctl --user {verb} {SERVICE}"], changes)

    def test_cancelled_settings_dialog_changes_nothing(self):
        box = self.sandbox()
        result = box.launcher("manage", STUB_ZENITY_RC="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        verbs = {c.split()[2] for c in box.calls() if c.startswith("systemctl")}
        self.assertLessEqual(verbs, {"is-active", "is-enabled"})


class RenderedLauncherTests(unittest.TestCase):
    """The installed .desktop files, as install.sh renders them."""

    def render(self, template, destination, executable):
        subprocess.run(
            [
                "bash", "-c",
                'source "$1"; shift; python_bin=/usr/bin/python3; '
                'render_desktop_entry "$@"',
                "test", str(HELPERS),
                str(ROOT / "desktop" / template), str(destination), str(executable),
            ],
            check=True,
            capture_output=True,
        )
        parser = configparser.ConfigParser(interpolation=None, delimiters=("=",))
        parser.optionxform = str
        parser.read(destination, encoding="utf-8")
        return parser

    def test_entries_run_the_launcher_with_the_intended_subcommands(self):
        box = Sandbox()
        self.addCleanup(box.cleanup)
        out = Path(box.directory.name)
        main = self.render("uu-remote.desktop.in", out / "main.desktop", box.executable)
        manage = self.render(
            "uu-remote-manage.desktop.in", out / "manage.desktop", box.executable
        )
        exe = str(box.executable)

        def argv(parser, section):
            return shlex.split(parser[section]["Exec"])

        # Opening and the dialog are only checked, not run: they start Wine
        # or need a display.
        self.assertEqual([exe, "open"], argv(main, "Desktop Entry"))
        self.assertEqual([exe, "manage"], argv(manage, "Desktop Entry"))
        self.assertEqual(
            "Quit;AutostartOn;AutostartOff;", main["Desktop Entry"]["Actions"]
        )
        actions = {
            "Desktop Action Quit": ([exe, "stop"], "stop"),
            "Desktop Action AutostartOn": ([exe, "autostart", "on"], "enable"),
            "Desktop Action AutostartOff": ([exe, "autostart", "off"], "disable"),
        }
        for section, (expected, verb) in actions.items():
            with self.subTest(section=section):
                self.assertEqual(expected, argv(main, section))
                box.log.write_text("")
                result = box.run(argv(main, section))
                self.assertEqual(result.returncode, 0, result.stderr)
                changes = [
                    c for c in box.calls() if c.startswith("systemctl")
                ]
                self.assertEqual([f"systemctl --user {verb} {SERVICE}"], changes)

    @unittest.skipUnless(shutil.which("desktop-file-validate"), "no validator")
    def test_rendered_entries_are_valid_desktop_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            for template in ("uu-remote.desktop.in", "uu-remote-manage.desktop.in"):
                destination = out / template.removesuffix(".in")
                self.render(template, destination, "/opt/uu/bin/uu-remote")
                result = subprocess.run(
                    ["desktop-file-validate", str(destination)],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class InstallerAutostartTests(unittest.TestCase):
    """install.sh keeps an earlier `autostart off` and installs zenity."""

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
        self.assertIn("prior=\n", result.stdout)
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

    def test_the_state_is_read_before_the_unit_file_is_written(self):
        source = INSTALLER.read_text()
        read = source.index('prior_autostart="$(bridge_autostart_state')
        write = source.index(
            'install -m 0644 "$repo_dir/systemd/uu-remote-bridge.service"'
        )
        refresh = source.index('refresh_bridge_autostart "$prior_autostart"')
        self.assertLess(read, write)
        self.assertLess(write, refresh)
        self.assertNotIn(f"reenable {SERVICE}", source)

    def test_package_install_requests_the_settings_dialog_dependency(self):
        source = INSTALLER.read_text()
        function = re.search(r"^install_packages\(\) \{\n.*?^\}\n", source, re.S | re.M)
        self.assertIsNotNone(function)
        script = (
            function.group(0)
            + 'sudo() { printf "%s\\n" "$*"; }\n'
            + "install_winehq() { :; }\ninstall_packages\n"
        )
        result = subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, timeout=30
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        installs = [
            line for line in result.stdout.splitlines()
            if line.startswith("apt-get install")
        ]
        self.assertEqual(1, len(installs), result.stdout)
        self.assertIn("zenity", installs[0].split())


if __name__ == "__main__":
    unittest.main()
