"""Generic live-desktop RDP sharing backend detection and lifecycle management."""
import logging
import os
import shutil
import signal
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from rdp_session_manager.infrastructure.commands import run_command
from rdp_session_manager.infrastructure.polkit import get_privilege_command

logger = logging.getLogger(__name__)

DEFAULT_LIVE_RDP_PORT = 3390

_BACKENDS: Dict[str, Dict[str, str]] = {
    "gnome-remote-desktop": {
        "binary": "grdctl",
        "arch_pkg": "gnome-remote-desktop",
        "debian_pkg": "gnome-remote-desktop",
        "label": "GNOME Remote Desktop (PipeWire/Mutter)",
    },
    "krdp": {
        "binary": "krdpserver",
        "arch_pkg": "krdp",
        "debian_pkg": "krdp",
        "label": "KDE Remote Desktop (PipeWire/KWin)",
    },
    "wayvnc": {
        "binary": "wayvnc",
        "arch_pkg": "wayvnc",
        "debian_pkg": "wayvnc",
        "label": "WayVNC (wlroots)",
    },
    "freerdp-shadow": {
        "binary": "freerdp-shadow-cli3",
        "arch_pkg": "freerdp",
        "debian_pkg": "freerdp3-shadow-x11",
        "label": "FreeRDP Shadow (X11)",
    },
}


def detect_live_session_backend(env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Detect the best live-desktop sharing backend for the active graphical session."""
    source = env if env is not None else os.environ
    session_type = (source.get("XDG_SESSION_TYPE") or "").strip().lower()
    desktop = (source.get("XDG_CURRENT_DESKTOP") or "").strip().lower()

    if session_type == "wayland":
        if "gnome" in desktop:
            backend = "gnome-remote-desktop"
        elif "kde" in desktop or "plasma" in desktop:
            backend = "krdp"
        else:
            backend = "wayvnc"
    else:
        backend = "freerdp-shadow"

    meta = _BACKENDS[backend]
    return {
        "backend": backend,
        "session_type": session_type or "x11",
        "desktop": desktop or "unknown",
        "binary": meta["binary"],
        "arch_pkg": meta["arch_pkg"],
        "debian_pkg": meta["debian_pkg"],
        "label": meta["label"],
    }


def is_backend_installed(backend: str) -> bool:
    meta = _BACKENDS.get(backend)
    if not meta:
        return False
    if backend == "freerdp-shadow":
        return bool(shutil.which("freerdp-shadow-cli3") or shutil.which("freerdp-shadow-cli"))
    return shutil.which(meta["binary"]) is not None


def _detect_distro_family() -> str:
    os_release = Path("/etc/os-release")
    if not os_release.exists():
        return "arch"
    content = os_release.read_text(encoding="utf-8", errors="ignore").lower()
    if any(token in content for token in ("arch", "cachyos", "manjaro", "endeavouros")):
        return "arch"
    if any(token in content for token in ("debian", "ubuntu", "linuxmint", "pop")):
        return "debian"
    return "arch"


def get_install_command(backend: str) -> List[str]:
    meta = _BACKENDS[backend]
    family = _detect_distro_family()
    _, priv_cmd = get_privilege_command()
    if family == "debian":
        return priv_cmd + ["apt-get", "install", "-y", meta["debian_pkg"]]
    return priv_cmd + ["pacman", "-S", "--noconfirm", "--needed", meta["arch_pkg"]]


def install_backend(backend: str) -> bool:
    cmd = get_install_command(backend)
    result = run_command(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        logger.error("Failed to install %s: %s", backend, result.stderr)
        return False
    return is_backend_installed(backend)


def _pid_file() -> Path:
    return Path.home() / ".config" / "rdp-session-manager" / "live_rdp.pid"


def _ensure_grd_tls() -> tuple[Path, Path]:
    cert_dir = Path.home() / ".local" / "share" / "gnome-remote-desktop"
    cert_dir.mkdir(parents=True, exist_ok=True)
    cert_path = cert_dir / "rdp-tls.crt"
    key_path = cert_dir / "rdp-tls.key"
    if not (cert_path.exists() and key_path.exists()):
        run_command(
            [
                "openssl", "req", "-new", "-newkey", "rsa:2048", "-days", "3650",
                "-nodes", "-x509", "-subj", "/CN=rdp-session-manager",
                "-out", str(cert_path), "-keyout", str(key_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    return cert_path, key_path


def start_live_rdp(
    username: str,
    port: int = DEFAULT_LIVE_RDP_PORT,
    password: str = "",
    backend: Optional[str] = None,
) -> bool:
    info = detect_live_session_backend() if backend is None else {"backend": backend}
    chosen = info["backend"]

    if chosen == "gnome-remote-desktop":
        cert_path, key_path = _ensure_grd_tls()
        commands = [
            ["grdctl", "rdp", "set-tls-cert", str(cert_path)],
            ["grdctl", "rdp", "set-tls-key", str(key_path)],
            ["grdctl", "rdp", "set-port", str(port)],
        ]
        if password:
            commands.append(["grdctl", "rdp", "set-credentials", username, password])
        commands.append(["grdctl", "rdp", "disable-view-only"])
        commands.append(["grdctl", "rdp", "enable"])
        commands.append(["systemctl", "--user", "restart", "gnome-remote-desktop.service"])
        for cmd in commands:
            res = run_command(cmd, capture_output=True, text=True, timeout=30)
            if res.returncode != 0:
                logger.error("grdctl/systemctl command %s failed: %s", cmd, res.stderr)
                return False
        return True

    if chosen == "krdp":
        stop_live_rdp(chosen)
        cmd = ["krdpserver", "--port", str(port), "-u", username]
        if password:
            cmd.extend(["-p", password])
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        _pid_file().parent.mkdir(parents=True, exist_ok=True)
        _pid_file().write_text(str(proc.pid), encoding="utf-8")
        return True

    if chosen == "freerdp-shadow":
        stop_live_rdp(chosen)
        binary = shutil.which("freerdp-shadow-cli3") or shutil.which("freerdp-shadow-cli")
        if not binary:
            return False
        cmd = [binary, f"/port:{port}", "-sec-nla", "+auth"]
        if not password:
            cmd = [binary, f"/port:{port}", "-sec-nla", "-auth"]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        _pid_file().parent.mkdir(parents=True, exist_ok=True)
        _pid_file().write_text(str(proc.pid), encoding="utf-8")
        return True

    logger.error("Unsupported live desktop backend: %s", chosen)
    return False


def update_live_credentials(
    username: str,
    password: str,
    port: int = DEFAULT_LIVE_RDP_PORT,
    backend: Optional[str] = None,
) -> bool:
    return start_live_rdp(username, port=port, password=password, backend=backend)


def stop_live_rdp(backend: Optional[str] = None) -> bool:
    info = detect_live_session_backend() if backend is None else {"backend": backend}
    chosen = info["backend"]

    if chosen == "gnome-remote-desktop":
        run_command(["grdctl", "rdp", "disable"], capture_output=True, text=True, timeout=15)
        run_command(["systemctl", "--user", "stop", "gnome-remote-desktop.service"], capture_output=True, text=True, timeout=15)
        return True

    pid_path = _pid_file()
    if pid_path.exists():
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip())
            os.kill(pid, signal.SIGTERM)
        except (OSError, ValueError):
            pass
        try:
            pid_path.unlink()
        except OSError:
            pass
    return True


def is_live_rdp_running(backend: Optional[str] = None) -> bool:
    info = detect_live_session_backend() if backend is None else {"backend": backend}
    chosen = info["backend"]
    if chosen == "gnome-remote-desktop":
        res = run_command(
            ["systemctl", "--user", "is-active", "gnome-remote-desktop.service"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return res.returncode == 0 and res.stdout.strip() == "active"

    pid_path = _pid_file()
    if not pid_path.exists():
        return False
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False
