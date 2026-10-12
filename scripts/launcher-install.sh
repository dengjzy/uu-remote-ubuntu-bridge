#!/usr/bin/env bash
# Sourced installer helpers for the launcher entries and the start-at-login
# switch; no Wine or desktop side effects, and systemctl is passed in.

# Print the current enablement of the bridge service (enabled, disabled, ...),
# or nothing when the unit is not installed yet. Call this BEFORE the unit file
# is written: a freshly written, never enabled unit also reads as "disabled".
# usage: bridge_autostart_state SYSTEMCTL...
bridge_autostart_state() {
    "$@" is-enabled uu-remote-bridge.service 2>/dev/null || true
}

# Re-link the service so an updated unit takes effect, but keep a start-at-login
# choice made earlier with `uu-remote autostart off`. A new install has no prior
# state and starts at login. A systemctl failure is returned to the caller.
# usage: refresh_bridge_autostart PRIOR_STATE SYSTEMCTL...
refresh_bridge_autostart() {
    local prior="$1"
    shift
    if [[ "$prior" == disabled ]]; then
        printf '%s\n' \
            'Start at login stays off, as chosen earlier. Turn it on with: uu-remote autostart on'
        return 0
    fi
    "$@" reenable uu-remote-bridge.service
}

# usage: render_desktop_entry TEMPLATE DESTINATION EXECUTABLE
render_desktop_entry() {
    "${python_bin:-/usr/bin/python3}" - "$@" <<'PY'
import sys
from pathlib import Path

template, destination, executable = map(Path, sys.argv[1:])
escaped = str(executable).replace("\\", "\\\\").replace(" ", "\\ ")
rendered = template.read_text(encoding="utf-8").replace("@EXEC@", escaped)
destination.write_text(rendered, encoding="utf-8")
PY
}
