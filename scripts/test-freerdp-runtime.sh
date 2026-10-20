#!/usr/bin/env bash
# Offline startup/SSPI smoke test, not RDP or controller acceptance.
set -Eeuo pipefail
umask 077

if (($# != 4)); then
    printf 'usage: %s RUNTIME_DIR CLIENT_SHA256 SOURCE_COMMIT NEW_OUTPUT_DIR\n' "$0" >&2
    exit 2
fi
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
runtime="$(realpath -e -- "$1")"
expected_sha="$2"
expected_source="$3"
output="$(realpath -m -- "$4")"
[[ "$expected_sha" =~ ^[0-9a-f]{64}$ && "$expected_source" =~ ^[0-9a-f]{40}$ ]] || {
    printf 'Expected an exact SHA-256 and full source commit.\n' >&2
    exit 2
}
[[ ! -e "$output" && ! -L "$output" ]] || {
    printf 'Output directory must be new; existing evidence is never overwritten.\n' >&2
    exit 2
}
wine_bin="${UURB_WINE_BIN:-/opt/wine-stable/bin/wine}"
wineboot_bin="${UURB_WINEBOOT_BIN:-/opt/wine-stable/bin/wineboot}"
wineserver_bin="${UURB_WINESERVER_BIN:-/opt/wine-stable/bin/wineserver}"
cc="${MINGW_CC:-x86_64-w64-mingw32-gcc}"
printf '%s  %s\n' "$expected_sha" "$runtime/sdl-freerdp.exe" | sha256sum -c -
[[ -s "$runtime/.build-sha256" ]]
(cd "$runtime" && sha256sum -c .build-sha256)

for command in "$wine_bin" "$wineboot_bin" "$wineserver_bin" "$cc" \
    Xvfb xvfb-run xauth timeout sha256sum python3; do
    command -v "$command" >/dev/null || {
        printf 'missing test tool: %s\n' "$command" >&2
        exit 1
    }
done
mkdir -m 0700 -- "$output"
scratch="$(mktemp -d "$output/.runtime.XXXXXX")"
export WINEPREFIX="$scratch/wine"
cleanup() {
    local status=$?
    trap - EXIT INT TERM
    timeout 5 env WINEPREFIX="$scratch/wine" "$wineserver_bin" -k >/dev/null 2>&1 || true
    # Only this invocation's disposable prefix/runtime; logs remain in output.
    rm -rf -- "$scratch"
    exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
mkdir "$scratch/runtime"
for file in "$runtime"/*.dll "$runtime/sdl-freerdp.exe" "$runtime/ossl-modules"; do
    [[ "$(basename -- "$file")" == winpr-sspi-shim.dll ]] && continue
    [[ -e "$file" ]] && ln -s -- "$file" "$scratch/runtime/"
done
"$cc" -std=c11 -O2 -Wall -Wextra -Werror -Wl,--no-insert-timestamp -shared \
    -o "$scratch/runtime/winpr-sspi-shim.dll" "$repo_dir/src/winpr_sspi_shim.c"
"$cc" -std=c11 -O2 -Wall -Wextra -Werror -Wl,--no-insert-timestamp \
    -o "$scratch/runtime/sspi-probe.exe" "$repo_dir/tests/probes/uu_freerdp_sspi_probe.c"
export WINEARCH=win64 WINEDEBUG=-all
export WINEDLLOVERRIDES='mscoree,mshtml,winemenubuilder.exe=d'
export SDL_RENDER_DRIVER=software
unset WAYLAND_DISPLAY OPENSSL_CONF OPENSSL_MODULES
# No connection arguments or real accounts. All Wine commands use a fresh
# prefix and a temporary X server; the installed bridge is never invoked.
xvfb-run -a --server-args='-screen 0 1024x768x24 -nolisten tcp' \
    bash -s -- "$wine_bin" "$wineboot_bin" "$scratch/runtime" "$output" "$expected_source" <<'SH'
set -Eeuo pipefail
cd -- "$3"
export OPENSSL_MODULES=ossl-modules
timeout 40 "$2" -u >"$4/wineboot.log" 2>&1
for option in version buildconfig help; do
    timeout 15 "$1" ./sdl-freerdp.exe "/$option" >"$4/client-$option.log" 2>&1
done
timeout 15 "$1" ./sspi-probe.exe "$5" >"$4/sspi.log" 2>&1
SH
python3 - "$output/client-version.log" "$expected_source" <<'PY'
from pathlib import Path
import re
import sys

text = Path(sys.argv[1]).read_text()
revisions = re.findall(r"\(([0-9a-f]{8,40})\)", text)
if not revisions or not all(sys.argv[2].startswith(value) for value in revisions):
    raise SystemExit("client source revision mismatch")
PY
printf '%s\n' \
    'PASS: pinned client starts; matching WinPR and shim produce first ANSI/Unicode negotiation tokens.' \
    'Not tested here: network authentication, reconnect, mouse/keyboard, dictation or clipboard.'
