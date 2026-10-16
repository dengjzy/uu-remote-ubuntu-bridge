# Login, capture and FreeRDP contribution review — 2026-10-16

`uu-remote login` can reuse the managed UU window instead of stopping the
bridge and Wine prefix. This avoids disconnecting an incoming session merely
to open the account interface. The change is adapted from @dengjzy's PR #22,
with the same display/application/helper preflight as `uu-remote open`.
The existing console starts an absent bridge, waits for a starting bridge,
and reuses an available one. Viewer cleanup keeps its existing focus-restoration
path. Separate popup windows can still be clipped; this change does not claim
to fix all login-dialog rendering.

## Reviewed revisions and decisions

| Item | Revision / scope | Decision |
| --- | --- | --- |
| [PR #22](https://github.com/lachlanchen/uu-remote-ubuntu-bridge/pull/22) | `af9a161b534f0e5b0a54b3c369d58d00c426453c` | Integrate the non-disruptive login route separately; request changes on root capture and dependency distribution/qualification. |
| [PR #19](https://github.com/lachlanchen/uu-remote-ubuntu-bridge/pull/19) | `9ca86dc31cac8d61e4731b17bff1a1895ba26d3c` | Still open; the shape-boundary failure reproduces on this unchanged revision. |
| [Issue #16](https://github.com/lachlanchen/uu-remote-ubuntu-bridge/issues/16) | Expired FreeRDP nightly | Still open. Build 2101 is an identifiable candidate, not a durable or runtime-qualified replacement. |
| [Issue #14](https://github.com/lachlanchen/uu-remote-ubuntu-bridge/issues/14) | Ubuntu ports and controller improvements | Keep as the collaboration tracker. No new 22.04/26.04 platform acceptance is established here. |
| [Issue #12](https://github.com/lachlanchen/uu-remote-ubuntu-bridge/issues/12) | ARM64 / Oracle VPS | Keep as compatibility tracking. No new test-host evidence; the x86-64 guard remains intentional. |

## Why `-sid` is not a dialog boundary

The installed x11vnc 0.9.16 help describes `-sid` as a shifted root view. It
captures the screen at the window's position; it does not select only that
application's descendants. Popups outside the selected rectangle remain
clipped. See also [upstream x11vnc help](https://github.com/LibVNC/x11vnc/blob/master/src/help.c).

An isolated Xvfb test placed a green 900×600 fixture at +100+100 over a red,
pointer-logging relay fixture. A 100×100 X Shape hole was cut in the green
window's upper-right corner. Running PR #22's actual `open_window` path with
stubbed bridge discovery and a test RFB viewer produced:

| Exporter | Red relay pixels in the image | RFB click at (850,50) |
| --- | ---: | --- |
| Existing `-id` | 0 | Reached the relay at (950,150) |
| Proposed `-sid` | 9,906 | Reached the relay at (950,150) |
| PR #19 opt-in region | 9,906 | Reached the relay at (950,150) |

The exact pixel count depends on the cursor. The important distinction is
that `-sid` adds visible relay pixels in this fixture. **The existing `-id`
path also forwards clicks through the hole. It must not be described as an
input sandbox.** Retaining it avoids expanding capture while the controller
is redesigned; it does not resolve that older input limitation. This is a
local controller-window fixture, not evidence of missing characters in an
incoming phone or physical-keyboard session.

The eventual popup solution needs a surface isolated from the live incoming
desktop relay, or equivalent pixel and input enforcement. Tests must cover
shape/transparency, focus, out-of-bounds events, window movement and hiding,
plus simultaneous incoming/outgoing control. Faster geometry polling alone
does not address a permanent shape hole.

### Reproduce without a production desktop

Dependencies include Xvfb, x11vnc, xdotool, Python Xlib, and the GTK dependencies
expected by PR #19's harness (`python3-gi`, GTK 3 and `python3-gi-cairo`).
Use only the reviewed revisions below. The probes create and clean up their
own X servers and fixture processes; no Wine prefix or user service is used.

```bash
git fetch origin pull/19/head pull/22/head
git worktree add --detach /tmp/uur-review19 9ca86dc31cac8d61e4731b17bff1a1895ba26d3c
git worktree add --detach /tmp/uur-review22 af9a161b534f0e5b0a54b3c369d58d00c426453c
/usr/bin/python3 docs/reviews/probes/compare-pr22-capture.py /tmp/uur-review19 /tmp/uur-review22
/usr/bin/python3 docs/reviews/probes/check-pr19-shape.py /tmp/uur-review19
```

Both probes intentionally fail when they reproduce the proposed capture
boundary violation. They report synthetic coordinates, never private input.
Afterwards, remove the two disposable worktrees with `git worktree remove`.

## FreeRDP 2101: provenance verified, acceptance pending

The proposed artifact was retrieved from the official Jenkins endpoint on
2026-10-16. Its 16,056,320 bytes hash to:

```text
0976457fbbb27b970de1aaf92a48474e1168efc3230ae271c7d0dc56e2bda2fd
```

[Build 2101 metadata](https://ci.freerdp.com/job/freerdp-nightly-windows/2101/api/json)
reports success and source revision
`5c8aac73cd293d44022c5ccfe36fd6f266b17098`, matching the proposed WinPR source
pin. The [Windows artifact](https://ci.freerdp.com/job/freerdp-nightly-windows/arch=win64,label=vs2017/2101/artifact/install/bin/sdl-freerdp.exe)
was available during this review. Availability and hash/source alignment do
not establish runtime compatibility or future availability.

Before making it the default:

1. Retain an approved artifact at a durable, versioned location with source
   provenance and applicable notices, or supply a pinned reproducible build.
2. Build and verify the matching WinPR runtime and dependencies.
3. Exercise that exact pair under Wine: connection/reconnection, mouse
   coordinates, modifiers, US/JIS symbols, phone text, Chinese/English
   dictation with multiline preservation, clipboard, and startup/restart.
4. Keep exact-hash verification, preflight-before-stop and rollback behavior.

No `lastSuccessfulBuild` fallback or relaxed hash acceptance was added. The
[existing recovery guide](../fresh-install-recovery.md) still applies: X11
users can choose the VNC relay, while RDP installations need an accepted client.

## Validation and deployment scope

The submitted PR #22 passed its 231-test suite (two opt-in tests skipped).
That did not catch the capture regression: its old source-string assertion
also matched a comment containing `-id`. A new regression records the actual
exporter command arguments. Other added tests check login/open delegation,
quoting, failure propagation, and bridge reuse/start/readiness behavior.

The integration passes 239 unit tests (two opt-in tests skipped), shell syntax,
Python compilation, compatibility-tool compilation, uninstall dry-run and
`git diff --check`. The new command-argument test was also run against PR #22
and failed on its actual `-sid` argument, as intended.

A read-only quick runtime check, allowing the expected source/runtime
difference, reported one existing discrepancy: the cursor guard is disabled
in saved configuration but remains mapped in the running process from an
earlier test. The service was left running; the saved setting takes effect
at its next normal restart. This check is therefore **not** an all-green
runtime acceptance result. The source changes neither install nor unload
that guard.

The profile README audit also reports pre-existing documentation gaps: no
`CITATION.cff`, navigation-format differences, and shorter translated READMEs
that do not cover all English sections/commands. This focused integration
does not claim to complete those translations or change the README set.

This review changes the launcher and review/test material. It does not alter
the installed UU binaries, input/dictation/clipboard patches, relay selection,
desktop size, or running service. Live acceptance of the new FreeRDP binary
and popup exporter remains unclaimed.
