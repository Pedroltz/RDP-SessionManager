"""Mode-specific RDP prerequisites and credential-free client diagnostics."""
import grp
import pwd
import subprocess
from .commands import run_command
from .polkit import get_privilege_command


def has_rdp_group(username):
    try:
        group = grp.getgrnam('rdp-users')
        return username in group.gr_mem or pwd.getpwnam(username).pw_gid == group.gr_gid
    except KeyError:
        return False


def repair_group(username):
    pwd.getpwnam(username)
    _, privilege = get_privilege_command()
    result = run_command(privilege + ['usermod', '-aG', 'rdp-users', username], capture_output=True)
    if result.returncode:
        raise RuntimeError('Could not repair XRDP access. Check administrator authorization and that the rdp-users group exists.')


def has_local_session(username):
    try:
        result = run_command(['loginctl', 'list-sessions', '--no-legend'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) < 3 or fields[2] != username:
                continue
            detail = run_command(['loginctl', 'show-session', fields[0], '-p', 'Remote', '-p', 'Type', '-p', 'State'], capture_output=True, text=True).stdout
            if 'Remote=no' in detail and ('Type=wayland' in detail or 'Type=x11' in detail) and 'State=closing' not in detail:
                return True
    except (OSError, subprocess.SubprocessError):
        pass
    return False


def connection_error(output):
    text = output.lower()
    if 'rdp-users' in text:
        return 'XRDP denied group access. Use Repair access for this user; Live Desktop Sharing does not require rdp-users.'
    if any(token in text for token in ('logon_failure', 'authentication_failed', 'message_altered', 'mic verification')):
        return 'Authentication failed. For Live Desktop Sharing, use the sharing password rather than your Linux password. Reset it with Change RDP Password if needed.'
    if 'graphics pipeline' in text or 'capabilities' in text:
        return 'Graphics negotiation failed. Live Desktop Sharing requires a FreeRDP client with Graphics Pipeline support.'
    if any(token in text for token in ('connect_failed', 'connection refused', 'timed out', 'transport_failed')):
        return 'The RDP service could not be reached. Check that sharing is enabled, the address and port are correct, and the firewall allows your local network.'
    return 'The RDP client closed with an error. Check the service status and credentials, then try again.'
