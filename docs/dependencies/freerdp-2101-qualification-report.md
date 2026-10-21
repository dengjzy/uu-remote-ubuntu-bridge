# FreeRDP Build 2101 Runtime Qualification Report

* **Date**: 2026-10-21
* **Status**: Contributor-reported acceptance evidence; interactive checks not independently reproduced by the bridge maintainer
* **Reporter / source**: [dengjzy, PR #24](https://github.com/lachlanchen/uu-remote-ubuntu-bridge/pull/24#issuecomment-6311428479)
* **Candidate**: FreeRDP nightly build 2101 (`sdl-freerdp.exe`) + matching WinPR runtime
* **Planned Release Tag**: `deps-freerdp-5c8aac73c-win64-r1`

---

## 1. Test Environment & Tested Artifacts

* **Host Operating System**: Ubuntu 24.04 LTS (x86_64, Linux 6.8.0)
* **Desktop Environment**: GNOME 46 (X11 backend for UU Remote display)
* **Display Output**: Native 1920x1200 (16:10 aspect ratio)
* **Wine Version**: `wine-11.0` (vanilla Wine package)
* **Bridge Git Baseline**: Contributor reports the PR #24 branch based on `6af4472`; the exact tested HEAD was not separately specified. This report was submitted in `5e9ca037832d1033e16c90f496ee13f241a0d698`.

### Contributor-reported Binary Checksums (SHA-256)

```text
0976457fbbb27b970de1aaf92a48474e1168efc3230ae271c7d0dc56e2bda2fd  sdl-freerdp.exe (build 2101, commit 5c8aac73cd293d44022c5ccfe36fd6f266b17098)
8832ad7e5ae1d4414c844065f3bfce065d1b1f4f77ae8ce7e46de9b5792a3d7c  libwinpr3.dll (source commit 5c8aac73cd293d44022c5ccfe36fd6f266b17098)
1b8a87de4c726eb629162361f5032ba0b045d101ad334b84e4a180660c1aa8ac  winpr-sspi-shim.dll (compiled locally from bridge tree)
4d2e724eb852f78ec0adbd1b7265325f79f503c9572658a26434f27f0cedb051  libcrypto-3-x64.dll (MSYS2 mingw-w64-x86_64-openssl 3.6.3-1)
b0aaaab67558716ea8cb03516d0e83ab92d1c0e3ddfc774c466032053f8b2331  libssl-3-x64.dll (MSYS2 mingw-w64-x86_64-openssl 3.6.3-1)
bbe224df64e6c834c2df4a4505d0af3826b951d78a93cff4429d2dd6ae41ae44  ossl-modules/legacy.dll (MSYS2 mingw-w64-x86_64-openssl 3.6.3-1)
71a09f78d94ecee3f4002161e9b740ecf82c0c321501ce111bb8b5bc52f85a4e  libcjson-1.dll (MSYS2 mingw-w64-x86_64-cjson 1.7.19-1)
b760714d224f86fb3cb2c2d6229d0e631a2b5779d6533c920e189e356faad451  liburiparser-1.dll (MSYS2 mingw-w64-x86_64-uriparser 1.0.2-1)
```

---

## 2. Interactive Acceptance Scenarios & Findings

### 2.1 Connection and Session Lifecycle
* **RDP / NLA Authentication**: **PASS**
  * Synthetic and live NLA authentication through `winpr-sspi-shim.dll` successfully established the RDP session into the local X11 desktop relay.
* **Reconnects & Session Stability**: **PASS**
  * Performed 5 consecutive disconnect and reconnect sequences from both desktop client and mobile remote app. Session re-attached cleanly with no orphan Wine processes or memory leaks.
* **Lock / Power State Recovery**: **PASS**
  * Maintained session integrity across prolonged idle periods with display sleep management inhibited.

### 2.2 Display Geometry & Pointer Control
* **Resolution & Scaling**: **PASS**
  * Tested at 1920x1200 resolution. Client frame buffer rendered with accurate aspect ratio, without pillarboxing or edge clipping.
* **Mouse Navigation & Modifiers**: **PASS**
  * Mouse coordinates mapped 1:1 across the whole desktop canvas. Left, right, middle buttons, drag-select, and vertical/horizontal wheel scrolling functioned smoothly.
  * Modifier combinations (`Shift+Click`, `Ctrl+Click`, `Alt+Drag`, `Super`) passed accurately to host window manager and applications.
* **Cursor Guard Integration**: **PASS**
  * Unconstrained pointer escapes during active capture were prevented.

### 2.3 Keyboard Layouts & Symbol Combinations
* **US Standard Keyboard Layout**: **PASS**
  * Verified all standard alphanumeric keys and ASCII symbol combinations:
    ```text
    ~ ! @ # $ % ^ & * ( ) _ + { } | : " < > ? [ ] \ ; ' , . / ` - =
    ```
  * Special chord shortcuts (`Ctrl+C`, `Ctrl+V`, `Ctrl+Z`, `Alt+F4`, `Ctrl+Alt+T`) functioned as expected.
* **JIS Keyboard Layout Hardware Scan Codes**: **NOT TESTED**
  * Only standard US physical layout hardware was connected during testing. Physical JIS-specific hardware keys (`¥`, `_` on JIS position, Henkan/Muhenkan, Kana) were **not exercised**.

### 2.4 Multiline IME Dictation
* **Continuous Multiline Chinese IME Input**: **PASS**
  * Tested continuous Pinyin text entry across multiple lines in bash terminal, text editors, and web browser inputs.
  * Verified that committing candidate words via Space / Enter does **not** overwrite, truncate, or replace existing text on previous lines or earlier words on the same line.
* **Mobile Virtual Keyboard Input**: **PASS**
  * Mobile client soft-keyboard dictation (both English and Chinese) streamed text cleanly without dropped characters.

### 2.5 Bi-directional Clipboard
* **Host to Remote Controller**: **PASS**
  * Copied multiline UTF-8 text from Ubuntu host (`gedit`) and pasted into remote client application.
* **Remote Controller to Host**: **PASS**
  * Copied text on the controller client and pasted into terminal/editor on Ubuntu host.

### 2.6 Service Lifecycle & Rollback
* **Service Control**: **PASS**
  * `systemctl --user {start|stop|restart} uu-remote-bridge.service` executed cleanly.
  * Stale X11 lock files and socket handles were properly released on shutdown.
* **Runtime Rollback**: **PASS**
  * Tested simulated rollback to prior runtime binaries: reverting binaries in the prefix and issuing a service restart restored working state without persistent corruption.

---

## 3. Summary of Contributor-reported Status

| Category | Status | Notes |
|:---|:---|:---|
| NLA Authentication & Connection | **PASS** | Verified end-to-end under Wine 11.0 |
| Session Reconnects | **PASS** | Repeated reconnect cycles verified |
| 1920x1200 Display & Cursor Guard | **PASS** | Native geometry, 1:1 mapping |
| US Symbol Combinations | **PASS** | Full ASCII symbol set verified |
| JIS Hardware Scan Codes | **NOT TESTED** | Hardware not available during test |
| Multiline Chinese IME Dictation | **PASS** | Verified no text overwrite across lines |
| Bi-directional Clipboard | **PASS** | UTF-8 text sync in both directions |
| Service Lifecycle & Rollback | **PASS** | Daemon lifecycle and fallback verified |

*Notice: This report documents contributor-observed acceptance results and remains labelled contributor-tested unless independently verified by upstream maintainers.*

## 4. Maintainer comparison and release scope

The reported client checksum matches the retained official executable. The
reported WinPR DLL hash differs from the maintainer's separately built DLL in
[the candidate record](freerdp-2101-candidate.json); this report does not establish
that those builds are byte-identical. The reported binary hashes are preserved
as supplied and have not been checked against the contributor's installed files.

The maintainer's offline startup and first-token SSPI checks remain separate
from these interactive observations. Physical JIS keys were not exercised;
the Chinese multiline description covers IME composition, while the mobile
dictation report does not specify duration or multiline test steps. Those
details remain unconfirmed rather than being inferred as additional passes.

Recording this report does not change installer pins or approve release
publication. Exact dependency inventory/notices and the final acceptance
decision remain tracked in the candidate record and issue #16.
