#!/bin/bash
# Helper script to update RDP user profiles and .xsession dispatcher with pkexec/sudo
# Usage: pkexec helpers/update-rdp-user-profiles.sh USERNAME PROFILES_JSON_FILE

set -e

USERNAME="$1"
PROFILES_JSON_SRC="$2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/audit-lib.sh"
rdpsm_audit_on_exit user.profiles.update "$USERNAME"

if [ -z "$USERNAME" ] || [ -z "$PROFILES_JSON_SRC" ] || [ ! -f "$PROFILES_JSON_SRC" ]; then
    echo "Error: Invalid arguments"
    echo "Usage: $0 USERNAME PROFILES_JSON_FILE"
    exit 1
fi

HOME_DIR=$(getent passwd "$USERNAME" | cut -d: -f6)
if [ -z "$HOME_DIR" ] || [ ! -d "$HOME_DIR" ]; then
    echo "Error: Home directory for $USERNAME not found"
    exit 1
fi

# Validate and stage alongside the destination so readers see a complete JSON
# document, including when copying or changing ownership fails.
PROFILES_DEST="$HOME_DIR/.rdp_profiles.json"
PROFILES_TEMP="$(mktemp "$HOME_DIR/.rdp_profiles.XXXXXX")"
finish_profiles() {
    status=$?
    [ -z "$PROFILES_TEMP" ] || /usr/bin/rm -f -- "$PROFILES_TEMP"
    rdpsm_audit_finish "$status"
}
trap finish_profiles EXIT
/usr/bin/python3 -m json.tool "$PROFILES_JSON_SRC" > "$PROFILES_TEMP"
/usr/bin/chown "$USERNAME:rdp-users" "$PROFILES_TEMP"
# Profiles contain launch metadata and are readable by the management UI.
/usr/bin/chmod 644 "$PROFILES_TEMP"
/usr/bin/mv -fT -- "$PROFILES_TEMP" "$PROFILES_DEST"
PROFILES_TEMP=""

# Generate the single maintained session dispatcher.
"$SCRIPT_DIR/create-session-wrapper.sh" "$USERNAME" "$HOME_DIR"
if [ "$HOME_DIR" = "/opt/rdp-users/$USERNAME" ]; then
    /usr/bin/python3 "$SCRIPT_DIR/apply-user-resource.py" "$USERNAME"
fi

echo "OK Profiles and .xsession updated for $USERNAME"
