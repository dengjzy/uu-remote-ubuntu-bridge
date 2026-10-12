# Launcher and popup-viewer contribution review — 2026-10-12

Reviewed the actual PR heads against `ea777ba`, independently of their AI
provenance. These are bridge contributions, not vendor UU releases. The
installed audited UU bundle remains unchanged.

| Request | Reviewed head | Decision |
| --- | --- | --- |
| [#18](https://github.com/lachlanchen/uu-remote-ubuntu-bridge/pull/18): quit and autostart controls | `53ff55a46ddd5130cd168c02357106859118d498` | Integrate with the maintainer corrections below. Preserve the contributor's commits. |
| [#19](https://github.com/lachlanchen/uu-remote-ubuntu-bridge/pull/19): experimental region viewer | `9ca86dc31cac8d61e4731b17bff1a1895ba26d3c` | Keep open; do not deploy or enable region export. Its remaining pixel/input boundary is reproducibly unsafe. |

## What Kiro means here

Both PR descriptions say they were prepared with Kiro, an AI coding assistant,
and tested by the contributor. [Kiro's documentation](https://kiro.dev/docs/)
describes an AI development environment. Neither patch introduces a Kiro runtime
dependency, account, SDK or agent service. This disclosure describes the
contributor's development workflow; it is not evidence that NetEase UU Remote
itself uses Kiro. Changes are assessed on code and observed tests.

## PR #18: useful controls, plus two real boundary fixes

The contributor addressed the previous requests: disabling autostart survives
a normal reinstall, the redundant settings dialog and zenity dependency are
gone, launcher actions are tested against harmless command stubs, and all
eleven READMEs describe the commands. The 13 submitted launcher tests passed.

Further review reproduced:

1. `bridge_autostart_state` swallowed every `is-enabled` error. With a failed
   state probe followed by a successful service command, the installer called
   `reenable` and exited zero. It could lose an explicit off choice. The
   maintainer correction reads structured `LoadState`/`UnitFileState`, recognizes
   a genuinely missing unit, preserves disabled and runtime-only states, and
   stops on bus errors, masks and unrecognized states. It runs before stopping
   the working bridge or replacing the unit.
2. The inherited `Exec=/path/with\ space/uu-remote` rendering passed
   `shlex.split` and `desktop-file-validate`, but real `gio launch` failed with
   “Desktop file didn’t specify Exec field.” Shell parsing is not desktop-entry
   parsing. The correction follows the two escaping layers in the
   [desktop-entry Exec specification](https://specifications.freedesktop.org/desktop-entry/latest/exec-variables.html).
   A fixed `/usr/bin/env --` executable also avoids GLib's pre-expansion
   executable lookup rejecting a literal percent sign in a path. Real GIO
   tests launch only a temporary argument-recording script, including paths
   containing spaces, Unicode, quotes, dollar signs, backticks, `%f` and `\`.

`uu-remote autostart status` now preserves the service manager's exit status
instead of silently converting query errors into success. A disabled status
can therefore return nonzero normally. CI explicitly installs the small GLib
launcher and desktop validator packages so this boundary is exercised.

The combined source suite ran 231 tests with two opt-in skips. No live `stop`,
`restart`, autostart toggle, desktop logout or Wine upgrade was used to test the
controls. Updating just the launcher and desktop entry requires no service
restart; existing enabled-at-login behavior is preserved on the review host.

## PR #19: improvements acknowledged, isolation not established

The revised maximum-covered-rectangle algorithm handles the earlier L-shaped
bounding-box gap, and restarting x11vnc when the crop moves avoids the stale
pointer-origin behavior the contributor found. Opt-in defaults and explicit
limitations are improvements. They do not establish a pixel/input boundary.

A deterministic test on isolated displays placed a red, pointer-logging relay
under a green `gameviewer.exe` window. The latter was 900×600 at +100+100, with
a 100×100 X Shape hole at its upper-right corner. Geometry was unchanged and
the region tracker considered the whole rectangle covered. The real PR
`open_window` and real x11vnc exported 9,906 red relay pixels. A viewer click at
(850,50) reached the underlying relay as `relay press 950 150`. The cursor can
change the precise pixel count; **any** exposed relay pixels or relayed click
violates the proposed boundary. No real desktop was involved.

This is steady-state leakage, not just a race at window closure. Polling every
0.15 seconds cannot repair it because ordinary geometry does not expose X
Shape holes. Other unresolved cases include transparent pixels, focus changes,
coordinates outside the framebuffer, and window changes between polls. Scale
commands run synchronously inside the same tracker, so their retries can also
delay region checks; 0.15 seconds is a nominal sleep, not a hard reaction bound.
The README/CHANGELOG claims that the relay is “never” exposed or reachable are
therefore stronger than either the implementation or the PR's stated limits.

The submitted nine-test suite also needs the GTK Cairo foreign bridge:
`python3-gi-cairo`, not just `python3-gi`/`python3-cairo`. On a host without it,
the draw callback is suppressed by redirected stderr and the color assertion
fails against an unpainted window. Its dependency check currently misses this.
The repository CI also lacks x11vnc/xdotool for these tests. These environment
gaps must not be reported as a production runtime failure or hidden as proof
that isolation passes. The shape reproduction used plain Python Xlib instead
of GTK drawing, keeping that result independent of Cairo availability.

To make this mergeable:

- Establish an actual pixel and input boundary, preferably an isolated
  controller surface rather than a root-screen crop over a live desktop relay.
- Add shape/transparency, hide/move, focus and out-of-bounds input regressions,
  and run the necessary display dependencies in CI.
- Describe remaining limitations accurately and obtain real-session evidence
  for popups, remote control and scaled pointer mapping on the final revision.
- A smaller dock-icon change may be submitted independently; it need not carry
  the region-export machinery.

## Remaining issue requests

- [#16](https://github.com/lachlanchen/uu-remote-ubuntu-bridge/issues/16)
  still needs a durable, reviewed FreeRDP client artifact or a reproducible
  replacement. Neither PR supplies it. Keep the exact-hash override and X11
  VNC fallback; do not replace the pin with an unverified current nightly.
- [#12](https://github.com/lachlanchen/uu-remote-ubuntu-bridge/issues/12)
  requests ARM64/Oracle compatibility. There is no new end-to-end ARM evidence;
  the x86-64 requirement remains. A matching Ubuntu version alone is not CPU
  compatibility.
- [#14](https://github.com/lachlanchen/uu-remote-ubuntu-bridge/issues/14)
  is the ongoing invitation for independently tested ports and controller
  changes, not a claim that every proposed environment is supported.

## Reproduction

The reusable [shape fixture](probes/pr19-shape-window.py) and
[review probe](probes/check-pr19-shape.py) reproduce the blocking issue against
the reviewed checkout. The probe deliberately fails the invariant on that
head. It creates only disposable Xvfb displays and fixture windows and cleans
them up; it never loads the production Wine prefix or controls its desktop.

```bash
# Requires the PR #19 checkout and its tests/probes, plus system python3-xlib,
# Xvfb, x11vnc, xdotool and the dependencies detected by its fixture harness.
/usr/bin/python3 docs/reviews/probes/check-pr19-shape.py /path/to/pr19-checkout
```
