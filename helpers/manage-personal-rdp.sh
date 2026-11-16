#!/bin/bash
# Helper script to enable, disable, or remove RDP access for an existing personal OS user
# Usage: pkexec helpers/manage-personal-rdp.sh USERNAME <enable|disable|remove> [PROFILES_JSON_FILE]

set -euo pipefail

USERNAME="${1:-}"
ACTION="${2:-}"
PROFILES_JSON_SRC="${3:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/audit-lib.sh"
rdpsm_audit_on_exit "personal_rdp.${ACTION:-unknown}" "$USERNAME"

if [ -z "$USERNAME" ] || [ -z "$ACTION" ]; then
    echo "Error: Not enough arguments" >&2
    echo "Usage: $0 USERNAME <enable|disable|remove> [PROFILES_JSON_FILE]" >&2
    exit 1
fi

case "$ACTION" in
    enable|disable|remove) ;;
    *)
        echo "Error: Invalid action '$ACTION'. Use enable, disable, or remove." >&2
        exit 1
        ;;
esac

if ! /usr/bin/id "$USERNAME" >/dev/null 2>&1; then
    echo "Error: User $USERNAME does not exist" >&2
    exit 1
fi

USER_UID=$(/usr/bin/id -u "$USERNAME")
if [ "$USER_UID" -lt 1000 ]; then
    echo "Error: Refusing to configure personal RDP for system user $USERNAME (UID $USER_UID)" >&2
    exit 1
fi

HOME_DIR=$(getent passwd "$USERNAME" | cut -d: -f6)
if [ -z "$HOME_DIR" ] || [ ! -d "$HOME_DIR" ]; then
    echo "Error: Home directory for $USERNAME not found" >&2
    exit 1
fi

if [ "$HOME_DIR" = "/opt/rdp-users/$USERNAME" ] || [[ "$HOME_DIR" == /opt/rdp-users/* ]]; then
    echo "Error: $USERNAME is a managed /opt/rdp-users account, not a personal user" >&2
    exit 1
fi

remove_from_rdp_group() {
    if getent group rdp-users >/dev/null 2>&1; then
        if id -Gn "$USERNAME" | tr ' ' '\n' | grep -Fxq rdp-users; then
            /usr/sbin/gpasswd -d "$USERNAME" rdp-users >/dev/null
        fi
    fi
}

case "$ACTION" in
    enable)
        if ! getent group rdp-users >/dev/null 2>&1; then
            /usr/sbin/groupadd rdp-users
        fi
        if [ ! -d "/opt/rdp-users" ]; then
            /usr/bin/mkdir -p /opt/rdp-users
            /usr/bin/chmod 755 /opt/rdp-users
        fi

        /usr/sbin/usermod -aG rdp-users "$USERNAME"

        PRIMARY_GROUP=$(/usr/bin/id -gn "$USERNAME")
        XSESSION_FILE="$HOME_DIR/.xsession"
        XSESSION_BAK="$HOME_DIR/.xsession.rdpsm.bak"
        if [ -f "$XSESSION_FILE" ] && ! grep -q "rdpsm-session.py" "$XSESSION_FILE" 2>/dev/null; then
            if [ ! -e "$XSESSION_BAK" ]; then
                /usr/bin/cp -a "$XSESSION_FILE" "$XSESSION_BAK"
            fi
        fi

        if [ -n "$PROFILES_JSON_SRC" ] && [ -f "$PROFILES_JSON_SRC" ]; then
            PROFILES_DEST="$HOME_DIR/.rdp_profiles.json"
            PROFILES_TEMP="$(mktemp "$HOME_DIR/.rdp_profiles.XXXXXX")"
            /usr/bin/python3 -m json.tool "$PROFILES_JSON_SRC" > "$PROFILES_TEMP"
            /usr/bin/chown "$USERNAME:$PRIMARY_GROUP" "$PROFILES_TEMP"
            /usr/bin/chmod 644 "$PROFILES_TEMP"
            /usr/bin/mv -fT -- "$PROFILES_TEMP" "$PROFILES_DEST"
        fi

        "$SCRIPT_DIR/create-session-wrapper.sh" "$USERNAME" "$HOME_DIR"
        echo "OK Personal RDP enabled for $USERNAME"
        ;;
    disable)
        remove_from_rdp_group
        echo "OK Personal RDP disabled for $USERNAME (OS account untouched)"
        ;;
    remove)
        remove_from_rdp_group
        /usr/bin/rm -f -- "$HOME_DIR/.rdp_profiles.json"

        XSESSION_FILE="$HOME_DIR/.xsession"
        XSESSION_BAK="$HOME_DIR/.xsession.rdpsm.bak"
        XINITRC_FILE="$HOME_DIR/.xinitrc"

        if [ -L "$XINITRC_FILE" ] && [ "$(readlink -f "$XINITRC_FILE" 2>/dev/null || true)" = "$(readlink -f "$XSESSION_FILE" 2>/dev/null || true)" ]; then
            /usr/bin/rm -f -- "$XINITRC_FILE"
        fi

        if [ -f "$XSESSION_FILE" ] && grep -q "rdpsm-session.py" "$XSESSION_FILE" 2>/dev/null; then
            /usr/bin/rm -f -- "$XSESSION_FILE"
        fi

        if [ -f "$XSESSION_BAK" ] && [ ! -e "$XSESSION_FILE" ]; then
            /usr/bin/mv -f -- "$XSESSION_BAK" "$XSESSION_FILE"
        fi

        echo "OK Personal RDP removed for $USERNAME (OS account and home kept intact)"
        ;;
esac

exit 0
