# Viewer shutdown and dock identity review — 2026-10-20

The managed UU window now closes with `uu-remote stop`. Its exporter and
viewer no longer inherit the window lock, and cleanup bounds the wait for a
stuck exporter. The window uses `UU-Remote` as its X11 class, matching the
launcher's `StartupWMClass`; reopening the launcher activates that window.

These changes integrate the contributions in #25 and #26, with additional
process-identity checks and isolated runtime tests. The capture mode,
installed UU binaries, input, dictation, clipboard and network routing are
unchanged.

## Reviewed revisions

| Pull request | Revision | Decision |
| --- | --- | --- |
| [#25: window cleanup](https://github.com/lachlanchen/uu-remote-ubuntu-bridge/pull/25) | `dedd5938a7c2eb7f2c7ac3a8908d5a9767481ce9` | Integrate with stricter process identification. |
| [#26: dock identity](https://github.com/lachlanchen/uu-remote-ubuntu-bridge/pull/26) | `a6646d00c585e0aae66ce408c897c935d9890d59` | Integrate; include the retag helper in bounded cleanup and require the viewer tests in CI. |
| [#24: FreeRDP 2101](https://github.com/lachlanchen/uu-remote-ubuntu-bridge/pull/24) | `b0cda8ea6486279a053592620af54068f4ed8464` | Changes requested: the proposed artifact already returns 404. |
| [#22: login, capture and FreeRDP](https://github.com/lachlanchen/uu-remote-ubuntu-bridge/pull/22) | `af9a161b534f0e5b0a54b3c369d58d00c426453c` | Superseded by the merged login fix in #23 and dependency follow-up #24; root capture remains unaccepted. |
| [#19: region capture](https://github.com/lachlanchen/uu-remote-ubuntu-bridge/pull/19) | `9ca86dc31cac8d61e4731b17bff1a1895ba26d3c` | Keep open with the existing capture-boundary changes requested. Its separate dock improvement is covered by #26. |

The revisions of #19 and #22 have not changed since the
[October 16 capture review](2026-10-16-login-capture-freerdp.md). The earlier
shape-hole results still apply; they were not rerun or presented as new
platform qualification. In particular, retaining `-id` avoids the additional
pixel exposure of root capture, but does not make it an input sandbox.

## Shutdown must identify a process, not a matching phrase

The submitted #25 implementation flattened a process's argument list and
searched for `uu-remote-console window`. A synthetic unrelated Python process
with that phrase as an argument was terminated when its PID was written to
the marker. It exited from SIGTERM during the reproduction.

The integrated implementation records both the PID and kernel start time.
Before stopping the window helper, it verifies the UID, start time, exact
resolved script path and `window` command as separate arguments. A Linux
process descriptor pins the process being signaled, avoiding a check/signal
race if its numeric PID is reused.

Child cleanup also verifies the parent PID and owner before signaling through
a process descriptor. This matters for the short-lived dock-retag helper:
its old PID can be reused while the viewer remains open. Each child gets up
to two seconds after TERM before KILL. The external close request gives the
window helper eight seconds to finish its cleanup.

The runtime marker's format is now `PID START_TICKS`. Missing, malformed,
legacy single-PID and stale markers are ignored. Normal opening writes the
new format; cleanup removes it. No process-name-wide kill is used.

## Runtime tests

The isolated fixture starts Xvfb, Openbox, a synthetic GTK application,
x11vnc and TigerVNC. It uses temporary HOME/runtime directories and ephemeral
loopback ports. Cleanup terminates only the fixture's own process groups.

The tests verify that:

- the real console gives the viewer the `UU-Remote` class;
- reopening reuses that viewer;
- stopping the console removes its viewer and releases the lock, including
  when its own x11vnc child is deliberately stopped with SIGSTOP;
- stale markers, unrelated arguments containing the helper name, and a
  reused child PID do not terminate unrelated processes.

The review host's generic `vncviewer` is RealVNC. To exercise the intended
TigerVNC path without replacing that application, the tests used a privately
extracted Ubuntu TigerVNC package and its FLTK libraries. This does not
establish RealVNC compatibility for the TigerVNC-specific launcher options.

On a test host with Ubuntu's TigerVNC package:

```bash
sudo apt-get install x11vnc xdotool x11-utils xvfb openbox \
  tigervnc-viewer python3-gi gir1.2-gtk-3.0
UURB_TEST_TIGERVNC=/usr/bin/xtigervncviewer \
UURB_REQUIRE_VIEWER_TESTS=1 \
  /usr/bin/python3 -m unittest discover -s tests -v
```

`UURB_TEST_TIGERVNC` is a test-fixture option, not a production setting.
CI installs the prerequisites and requires the fixture to run instead of
silently skipping it. The fixture verifies X11 window properties and reuse;
it does not substitute for a visual GNOME dock acceptance check.

Local validation ran 248 tests: 246 passed and two opt-in tests were skipped
(host clipboard integration and an isolated systemd recovery test). Both
viewer fixtures ran and passed. Shell syntax, Python compilation,
compatibility-tool compilation, uninstall dry-run and `git diff --check`
also passed.

## FreeRDP availability

On October 20 both the proposed
[build-2101 executable](https://ci.freerdp.com/job/freerdp-nightly-windows/arch=win64,label=vs2017/2101/artifact/install/bin/sdl-freerdp.exe)
and its [metadata](https://ci.freerdp.com/job/freerdp-nightly-windows/2101/api/json)
returned HTTP 404. Build 2064's artifact also remains unavailable.

The 2101 artifact was retrievable on October 16 and its hash and source
revision matched the proposal. That earlier verification does not make a
retention-limited nightly endpoint suitable for the default installer.
[Issue #16](https://github.com/lachlanchen/uu-remote-ubuntu-bridge/issues/16)
remains open. The next dependency proposal needs durable distribution or a
reproducible pinned build, applicable notices and source provenance, and
runtime qualification of the exact client/WinPR pair. Hash verification and
preflight-before-stop must remain intact.

## Deployment scope

This integration updates repository source and tests. It does not install
new helpers, replace the host VNC viewer, restart the bridge, or alter an
active desktop. Existing profile README/citation/translation audit gaps are
outside this focused change; no translation-completeness claim is made.

The quick installed-runtime check, allowing the expected source/runtime
difference, still reports the cursor-guard discrepancy recorded on October
16: the guard remains mapped despite the saved disabled setting. All other
checks completed successfully. The active service was preserved; this is not
an all-green live-runtime acceptance claim or a new controller-input test.
