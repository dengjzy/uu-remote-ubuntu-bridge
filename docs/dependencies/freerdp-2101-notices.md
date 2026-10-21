# Candidate Dependency Notices: FreeRDP Build 2101

This document records upstream third-party license notices, provenance, and
source file hashes for components identified in the retained Windows client
`sdl-freerdp.exe` (FreeRDP nightly build 2101) and companion WinPR runtime.

**Status**: Candidate reference collection prepared for dependency review. The
licensing prerequisite in [freerdp-2101-candidate.json](freerdp-2101-candidate.json)
remains pending until the exact build inventory and unmodified notices are
verified and accepted by upstream maintainers. See also
[Durable FreeRDP downloads](freerdp-release-hosting.md) and
[Runtime Qualification Report](freerdp-2101-qualification-report.md).

---

## 1. Candidate Artifact Identification

* **Filename**: `sdl-freerdp.exe`
* **Upstream Project**: FreeRDP ([github.com/FreeRDP/FreeRDP](https://github.com/FreeRDP/FreeRDP))
* **Version String**: `3.32.3-dev0 (5c8aac73c)`
* **Source Commit**: `5c8aac73cd293d44022c5ccfe36fd6f266b17098`
* **File Size**: `16,056,320` bytes
* **SHA-256**: `0976457fbbb27b970de1aaf92a48474e1168efc3230ae271c7d0dc56e2bda2fd`
* **Upstream CI Origin**: FreeRDP Jenkins CI `freerdp-nightly-windows/arch=win64,label=vs2017/2101`
* **Compiler Toolchain**: MSVC `19.16.27045.0` (Visual Studio 2017), Target Architecture `x64`
* **Build Configuration Flags** (extracted from binary strings):
  ```text
  Build type:          Release
  CFLAGS:              /DWIN32 /D_WINDOWS /W3 /O2 /Ob2 /DNDEBUG
  Compiler:            MSVC, 19.16.27045.0
  Target architecture: x64
  Key features:        WITH_CLIENT=ON WITH_CLIENT_SDL=ON WITH_CLIENT_SDL3=ON
                       WITH_SDL_LINK_SHARED=OFF WITH_SDL_IMAGE_DIALOGS=ON
                       WITH_OPENSSL=ON WITH_OPUS=ON WITH_URIPARSER=ON
                       WITH_WINPR_JSON=ON WITH_SMARTCARD_PCSC=ON
                       WITH_NATIVE_SSPI=ON WITH_AVX2=ON WITH_SIMD=ON
  ```

---

## 2. Identified Component Inventory

Dynamic imports of `sdl-freerdp.exe` are restricted exclusively to standard
Microsoft Windows system libraries (`KERNEL32.dll`, `USER32.dll`, `GDI32.dll`,
`IMM32.dll`, `WINMM.dll`, `ADVAPI32.dll`, `SHELL32.dll`, `ole32.dll`, etc.).
The import table does not enumerate statically linked libraries or prove that
optional runtime-loaded components are absent. The rows below are evidence for
review, not a complete binary bill of materials.

### 2.1 Components identified in the client

| Component | Upstream Project / Origin | Version / Context | SPDX License ID | Linkage |
|:---|:---|:---|:---|:---|
| **FreeRDP Core & SDL Client** | [FreeRDP/FreeRDP](https://github.com/FreeRDP/FreeRDP) | `3.32.3-dev0` (commit `5c8aac73c`) | Apache-2.0 | Static |
| **WinPR Core** | [FreeRDP/FreeRDP (winpr)](https://github.com/FreeRDP/FreeRDP/tree/master/winpr) | commit `5c8aac73c` | Apache-2.0 | Static |
| **SDL3** | [libsdl-org/SDL](https://github.com/libsdl-org/SDL) | 3.x (from `C:rdp\deps\SDL`) | Zlib | Static |
| **SDL3_ttf** | [libsdl-org/SDL_ttf](https://github.com/libsdl-org/SDL_ttf) | 3.x | Zlib | Static |
| **SDL3_image** | [libsdl-org/SDL_image](https://github.com/libsdl-org/SDL_image) | 3.x (from `C:rdp\deps\SDL_image`) | Zlib | Static |
| **OpenSSL** (embedded client crypto) | [openssl/openssl](https://github.com/openssl/openssl) | `3.6.2` (7 Apr 2026, built 2025-03-10, `VC-WIN64A`) | Apache-2.0 | Static |
| **Opus** | [xiph/opus](https://gitlab.xiph.org/xiph/opus) | CELT + SILK (from `C:rdp\deps\opus`) | BSD-3-Clause | Static |
| **FreeType 2** | [freetype/freetype](https://gitlab.freedesktop.org/freetype/freetype) | Bundled via SDL_ttf; version not established | FTL reference supplied; exact component review pending | Static |
| **HarfBuzz** | [harfbuzz/harfbuzz](https://github.com/harfbuzz/harfbuzz) | Bundled via SDL_ttf | MIT | Static |
| **libtiff** | [libtiff/libtiff](https://gitlab.com/libtiff/libtiff) | >= 4.5.1 (from `SDL_image\external\libtiff`) | libtiff | Static |
| **libpng** | [pnggroup/libpng](https://github.com/pnggroup/libpng) | Bundled via SDL_image (`1.6.56` string) | Libpng | Static |
| **zlib** | [madler/zlib](https://github.com/madler/zlib) | `1.3.1` (deflate 1.3.1) | Zlib | Static |
| **cJSON** | [DaveGamble/cJSON](https://github.com/DaveGamble/cJSON) | 1.x (FreeRDP WinPR json) | MIT | Static |
| **uriparser** | [uriparser/uriparser](https://github.com/uriparser/uriparser) | 1.x (FreeRDP URI parser) | BSD-3-Clause | Static |

### 2.2 Dynamically Loaded WinPR Runtime Companions

The candidate runtime uses the `scripts/build-winpr.sh` recipe from the
[candidate-pin commit](https://github.com/dengjzy/uu-remote-ubuntu-bridge/blob/c11d9699dbd72fc78595c9e68e663cb3f7977425/scripts/build-winpr.sh)
with MSYS2 MinGW-w64 packages. The current installer default is unchanged:

| File | Upstream Component | Version / Package | SPDX License ID | Linkage |
|:---|:---|:---|:---|:---|
| `libwinpr3.dll` | FreeRDP WinPR | Commit `5c8aac73cd293d44022c5ccfe36fd6f266b17098` | Apache-2.0 | Dynamic |
| `libcrypto-3-x64.dll` | OpenSSL Crypto | `mingw-w64-x86_64-openssl-3.6.3-1` | Apache-2.0 | Dynamic |
| `libssl-3-x64.dll` | OpenSSL SSL | `mingw-w64-x86_64-openssl-3.6.3-1` | Apache-2.0 | Dynamic |
| `ossl-modules/legacy.dll` | OpenSSL Legacy Provider | `mingw-w64-x86_64-openssl-3.6.3-1` | Apache-2.0 | Dynamic |
| `libcjson-1.dll` | cJSON | `mingw-w64-x86_64-cjson-1.7.19-1` | MIT | Dynamic |
| `liburiparser-1.dll` | uriparser | `mingw-w64-x86_64-uriparser-1.0.2-1` | BSD-3-Clause | Dynamic |
| `winpr-sspi-shim.dll` | UU Remote Bridge SSPI Shim | Local source compilation | MIT | Dynamic |

> **Note on OpenSSL versions:** The executable `sdl-freerdp.exe` contains
> statically linked OpenSSL 3.6.2 (reported by the retained upstream client with
> MSVC). The companion WinPR runtime uses OpenSSL 3.6.3 DLLs from MSYS2.
> Both belong to the OpenSSL 3.x series and are governed by the Apache License 2.0.

---

## 3. Verbatim source files and provenance

The [source manifest](freerdp-2101-licenses/sources.json) records immutable
upstream commit URLs and SHA-256 hashes. Each linked file below preserves the
downloaded bytes, including whitespace and final newlines. The offline test
checks every file against that manifest.

**Source verification is not binary inventory verification.** Entries marked
`reference-only-version-not-established` use a named upstream reference release
because the exact version embedded in build 2101 is still unknown. Their
license texts must not be described as a complete notice bundle for that binary.
Version/source-correlated entries match available source, version-string or
companion-package evidence; they do not prove the entire transitive inventory.

| Component | Source reference | File | Evidence scope |
| --- | --- | --- | --- |
| cJSON | `v1.7.19` | [Original file](freerdp-2101-licenses/DaveGamble-cJSON-v1.7.19-LICENSE) | Version/source-correlated; see inventory above |
| FreeRDP | `5c8aac73cd293d44022c5ccfe36fd6f266b17098` | [Original file](freerdp-2101-licenses/FreeRDP-FreeRDP-5c8aac73cd293d44022c5ccfe36fd6f266b17098-LICENSE) | Version/source-correlated; see inventory above |
| freetype | `VER-2-13-3` | [Original file](freerdp-2101-licenses/freetype-freetype-VER-2-13-3-FTL.TXT) | Reference version; embedded version unknown |
| harfbuzz | `10.0.1` | [Original file](freerdp-2101-licenses/harfbuzz-harfbuzz-10.0.1-COPYING) | Reference version; embedded version unknown |
| SDL | `release-3.2.0` | [Original file](freerdp-2101-licenses/libsdl-org-SDL-release-3.2.0-LICENSE.txt) | Reference version; embedded version unknown |
| SDL_image | `release-3.2.0` | [Original file](freerdp-2101-licenses/libsdl-org-SDL_image-release-3.2.0-LICENSE.txt) | Reference version; embedded version unknown |
| SDL_ttf | `release-3.2.0` | [Original file](freerdp-2101-licenses/libsdl-org-SDL_ttf-release-3.2.0-LICENSE.txt) | Reference version; embedded version unknown |
| libtiff | `v4.5.1` | [Original file](freerdp-2101-licenses/libsdl-org-libtiff-v4.5.1-LICENSE.md) | Reference version; embedded version unknown |
| zlib | `v1.3.1` | [Original file](freerdp-2101-licenses/madler-zlib-v1.3.1-LICENSE) | Version/source-correlated; see inventory above |
| openssl | `openssl-3.6.2` | [Original file](freerdp-2101-licenses/openssl-openssl-openssl-3.6.2-LICENSE.txt) | Version/source-correlated; see inventory above |
| openssl | `openssl-3.6.3` | [Original file](freerdp-2101-licenses/openssl-openssl-openssl-3.6.3-LICENSE.txt) | Version/source-correlated; see inventory above |
| libpng | `v1.6.56` | [Original file](freerdp-2101-licenses/pnggroup-libpng-v1.6.56-LICENSE) | Version/source-correlated; see inventory above |
| uriparser | `uriparser-1.0.2` | [Original file](freerdp-2101-licenses/uriparser-uriparser-uriparser-1.0.2-COPYING.BSD-3-Clause) | Version/source-correlated; see inventory above |
| opus | `v1.5.2` | [Original file](freerdp-2101-licenses/xiph-opus-v1.5.2-COPYING) | Reference version; embedded version unknown |

The libpng reference is 1.6.56, matching the version string in the retained
client. OpenSSL 3.6.2 and 3.6.3
are recorded separately. SDL, SDL_ttf and SDL_image each have their own source
license file. The libtiff source is the SDL project's upstream-derived fork;
its 4.5.1 reference does not establish the client's exact libtiff build.

The uriparser 1.0.2 library uses `COPYING.BSD-3-Clause`; its source tree also
contains separate licenses for tests and fuzzing code. This collection covers
the library reference, not redistribution of those development tools. The
bridge's own SSPI shim is covered by the repository [MIT license](../../LICENSE).

## 4. Publication status

The exact static dependency inventory and complete applicable notice bundle
remain pending. This collection preserves auditable source material for that
review. It does not authorize publication of the retained executable or switch
the installer default. Runtime observations are documented separately in the
[contributor report](freerdp-2101-qualification-report.md).
