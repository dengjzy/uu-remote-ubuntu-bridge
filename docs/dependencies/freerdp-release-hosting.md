# Durable FreeRDP downloads

FreeRDP Jenkins nightlies are temporary build outputs. Build 2064 expired;
the proposed replacement, build 2101, was downloadable on October 16, 2026
and returned 404 on October 20. Advancing the nightly number does not fix
fresh installation reliably.

The distribution path is a reviewed, versioned GitHub Release asset with an
exact SHA-256 pin. A later CI build can produce that asset from pinned source
and dependencies. End users should not need to cross-compile SDL and FreeRDP.

**Preparation is not approval.** The installer still uses its existing pins.
The [2101 candidate record](freerdp-2101-candidate.json) is evidence for a
dependency review; it is not consumed by the installer. The retained binary
has not passed full bridge acceptance and is not yet published for installation.

## Release contents

Assemble the dependency release as a draft, separate from bridge version tags.
The proposed tag is `deps-freerdp-5c8aac73c-win64-r1`. The final asset set needs:

- the exact executable accepted by runtime testing;
- a SHA-256 manifest and source revision;
- upstream origin, retrieval date, build configuration and toolchain provenance;
- the matching WinPR build recipe, runtime dependency versions and checksums;
- the licenses/notices required by the executable and its dependencies;
- a test report separating automated coverage from real-controller checks.

The existing installer builds WinPR separately and loads it through
`winpr-sspi-shim.dll`. Hosting only the SDL executable does not eliminate
those build dependencies. Changing their packaging is a separate change;
every delivered runtime file must be accounted for and tested.

The binary's build configuration reports static SDL3 linkage, OpenSSL and
Opus support, and SDL image dialogs. Strings also identify SDL_ttf, FreeType,
HarfBuzz and libtiff. This is evidence that the FreeRDP license alone is not
a complete notice bundle. These observations are documented and inventoried
with full third-party notices in [freerdp-2101-notices.md](freerdp-2101-notices.md).
The OpenSSL 3.6.2 string inside the client is separate from the OpenSSL 3.6.3
package used by the current WinPR build recipe.

GitHub release immutability was enabled for this repository on October 21.
It applies to future published releases; it does not retroactively lock the
existing bridge releases. Assemble every asset while the release is a draft,
then publish only after review. Do not mark this dependency release as the
latest bridge release. See [GitHub's immutability documentation](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
and [repository setting](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes).

## Offline runtime smoke test

Run against a trusted build output containing `sdl-freerdp.exe`,
`libwinpr3.dll`, its runtime DLLs, `ossl-modules/legacy.dll` and
`.build-sha256`:

```bash
scripts/test-freerdp-runtime.sh \
  /path/to/candidate-runtime \
  0976457fbbb27b970de1aaf92a48474e1168efc3230ae271c7d0dc56e2bda2fd \
  5c8aac73cd293d44022c5ccfe36fd6f266b17098 \
  /path/to/new-private-test-output
```

The helper validates the client and runtime hashes before creating anything.
The checksum manifest must cover exactly the files to stage, including every
DLL and provider file. Unlisted files, duplicate or unsafe manifest paths, and
symlinked provider directories are rejected. It copies the validated files into
the temporary runtime and checks those bytes again; the source directory is
not exposed to Wine. The recorded hashes remain with the test logs.
It compiles the current SSPI shim and a synthetic probe, starts a temporary
X server and fresh Wine prefix, and checks:

1. The client can report its version, build configuration and help.
2. The client and WinPR report the expected source revision.
3. Both ANSI and Unicode SSPI interfaces acquire synthetic outbound
   credentials and generate their first negotiation token.
4. Context and credential cleanup succeed.

No RDP connection or real account is used. Raw tokens and passwords are not
printed. The temporary Wine prefix and test runtime are removed on exit;
diagnostic logs remain in the requested new directory. Existing output is
never overwritten. Logs can include local paths, so review them before sharing.
The installed Wine prefix and running UU service are not used.

Defaults use Wine under `/opt/wine-stable/bin`; `UURB_WINE_BIN`,
`UURB_WINEBOOT_BIN` and `UURB_WINESERVER_BIN` can select another installation.
Use all three from the same Wine installation. The test also needs Xvfb,
`xvfb-run`, xauth, Python 3 and a MinGW C compiler.

### October 21 result

The official retained executable matched its 16,056,320-byte size and SHA-256.
A WinPR build from the matching source revision completed. Under Wine 11.0,
client startup and the offline ANSI/Unicode negotiation tests passed:

```text
WinPR revision=5c8aac73cd293d44022c5ccfe36fd6f266b17098
ANSI negotiate status=0x00090312 token-present=1
Unicode negotiate status=0x00090312 token-present=1
```

`SEC_I_CONTINUE_NEEDED` means the first negotiation token was produced. It
does not mean a server accepted authentication.

The upstream revision-detection helper reported `n/a` when building from a
Git worktree. For this isolated build, the verified full `git rev-parse HEAD`
value was written to FreeRDP's supported `.source_version` files in both the
source root and `winpr/`, then the library was rebuilt. This supplies build
provenance metadata; it does not change the checked-in source or the production
build script. The runtime checksum in the candidate record refers to that
rebuilt library.

The local suite ran 260 tests: 258 passed and the two existing opt-in tests
were skipped. The preflight regressions cover changed or unlisted runtime
files, invalid manifests, provider-directory symlinks, preservation of existing
evidence and acceptance of a complete inventory. The probe compiles with
warnings treated as errors. These checks do not expand the runtime acceptance
scope listed below.

## Before promotion

The offline smoke test deliberately does not certify connection, NLA
authentication, reconnect, pointer coordinates, modifiers, US/JIS symbols,
phone input, Chinese/English multiline dictation, clipboard, restart or
rollback. Exercise those with the exact executable/runtime pair before
changing `scripts/build-winpr.sh` and `scripts/verify.sh`.

After a complete draft is accepted:

1. Publish the immutable dependency release and download its asset again.
2. Check the downloaded bytes against the reviewed hash.
3. Update the client URL, client hash and WinPR source pin together in a
   focused installer PR. Keep the local exact-hash override.
4. Verify corrupt downloads fail before stopping a running bridge, and that
   VNC-only installs still skip this dependency.

Never follow `latest`, `lastSuccessfulBuild`, or a mutable replacement asset.
A failed candidate should leave a working installation running.

## Later: source builds in CI

A pinned cross-build is a separate follow-up. It needs a locked compiler,
SDL and other dependency inputs, recorded build flags and licenses, runtime
qualification and artifact provenance. Matching source commits alone do not
prove byte-for-byte reproducibility. CI can publish accepted outputs through
the same release channel, preserving a simple download-based installer.
