#!/usr/bin/env python3
"""Headless GTK activation/refresh/shutdown smoke for checkout or installed code."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

if '--installed' not in sys.argv:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gio, GLib
from rdp_session_manager.presentation.gtk.application import RDPSessionManagerApp

app = RDPSessionManagerApp()
app.set_flags(Gio.ApplicationFlags.NON_UNIQUE)
started = time.monotonic()
state = {'success': False}

def check():
    window = app.window
    if window is not None and window._last_health_report is not None and window.ip_row.get_subtitle():
        state.update(success=True, activation_refresh_ms=round((time.monotonic()-started)*1000), users=len(window._user_rows))
        screenshot = os.environ.get('RDPSM_GTK_SCREENSHOT')
        if screenshot:
            subprocess.run(['import', '-window', 'root', screenshot], check=True, timeout=10)
        window.close()
        app.quit()
        return False
    if time.monotonic() - started > 15:
        state['error'] = 'Window, health report, or dashboard did not become ready'
        app.quit()
        return False
    return True

GLib.timeout_add(100, check)
app.run([])
print(json.dumps(state))
raise SystemExit(0 if state['success'] else 1)
