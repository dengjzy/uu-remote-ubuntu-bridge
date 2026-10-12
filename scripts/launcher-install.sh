#!/usr/bin/env bash
# Sourced installer helpers for the launcher entries and the start-at-login
# switch; no Wine or desktop side effects, and systemctl is passed in.

# Print the enablement, or not-found for a genuinely absent unit. A failed
# manager query must never be mistaken for a fresh installation. Call this
# before stopping the bridge or writing its unit file.
# usage: bridge_autostart_state SYSTEMCTL...
bridge_autostart_state() {
    local properties load_state="" unit_state="" key value
    properties="$("$@" show uu-remote-bridge.service \
        --property=LoadState --property=UnitFileState)" || return "$?"
    while IFS='=' read -r key value; do
        case "$key" in
            LoadState) load_state="$value" ;;
            UnitFileState) unit_state="$value" ;;
        esac
    done <<<"$properties"
    if [[ "$load_state" == not-found && -z "$unit_state" ]]; then
        printf '%s\n' not-found
    elif [[ "$load_state" == loaded &&
            "$unit_state" =~ ^(enabled|enabled-runtime|disabled)$ ]]; then
        printf '%s\n' "$unit_state"
    else
        printf 'Cannot safely preserve UU autostart (load=%s, state=%s); inspect the user unit first.\n' \
            "${load_state:-unknown}" "${unit_state:-unknown}" >&2
        return 1
    fi
}

# Re-link the service so an updated unit takes effect, but keep a start-at-login
# choice made earlier with `uu-remote autostart off`. A new install has no prior
# state and starts at login. A systemctl failure is returned to the caller.
# usage: refresh_bridge_autostart PRIOR_STATE SYSTEMCTL...
refresh_bridge_autostart() {
    local prior="$1"
    shift
    case "$prior" in
        disabled)
            printf '%s\n' \
                'Start at login stays off, as chosen earlier. Turn it on with: uu-remote autostart on'
            ;;
        enabled|not-found) "$@" reenable uu-remote-bridge.service ;;
        enabled-runtime) "$@" reenable --runtime uu-remote-bridge.service ;;
        *) printf 'Unrecognized prior autostart state: %s\n' "$prior" >&2; return 1 ;;
    esac
}

# usage: render_desktop_entry TEMPLATE DESTINATION EXECUTABLE
render_desktop_entry() {
    "${python_bin:-/usr/bin/python3}" - "$@" <<'PY'
import sys
from pathlib import Path

template, destination, executable = map(Path, sys.argv[1:])
raw = str(executable)
if not executable.is_absolute() or any(ord(char) < 32 for char in raw):
    raise SystemExit("launcher executable must be an absolute path without control characters")
# Exec has two escaping layers: desktop-entry string escapes, then quoted
# argument parsing. Percent signs are field codes even inside quotes.
quoted = '"' + ''.join('\\' + char if char in '\\"`$' else char for char in raw) + '"'
# GIO checks the first executable before expanding %% field codes. A fixed
# env executable keeps a literal percent in the installed path launchable.
escaped = '/usr/bin/env -- ' + quoted.replace('\\', '\\\\').replace('%', '%%')
rendered = template.read_text(encoding="utf-8").replace("@EXEC@", escaped)
destination.write_text(rendered, encoding="utf-8")
PY
}
