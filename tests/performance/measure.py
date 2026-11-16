#!/usr/bin/env python3
"""Read-only host measurements; run from either side of a refactor."""
import json
import os
from pathlib import Path
import resource
import statistics
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from rdp_session_manager.infrastructure.session_monitor import SessionMonitor
from rdp_session_manager.infrastructure.user_manager import UserManager


def measure(callback, repeats=3):
    durations, cpu, commands = [], [], []
    run = subprocess.run
    for _ in range(repeats):
        count = 0
        def counted(*args, **kwargs):
            nonlocal count
            count += 1
            return run(*args, **kwargs)
        started, cpu_started = time.perf_counter(), time.process_time()
        with patch('subprocess.run', side_effect=counted):
            callback()
        durations.append((time.perf_counter() - started) * 1000)
        cpu.append((time.process_time() - cpu_started) * 1000)
        commands.append(count)
    return {'median_ms': round(statistics.median(durations), 3),
            'cpu_ms': round(statistics.median(cpu), 3),
            'subprocesses': statistics.median(commands)}


if __name__ == '__main__':
    monitor = SessionMonitor(cache_ttl=0)
    users = UserManager(app_config=None)
    result = {
        'cli_help': measure(lambda: subprocess.run(
            [sys.executable, str(ROOT / 'src/rdp_session_manager/presentation/cli/__main__.py'), '--help'],
            stdout=subprocess.DEVNULL, check=True)),
        'users': measure(users.list_users),
        'sessions': measure(monitor.get_active_sessions),
        'system_stats': measure(monitor.get_system_stats),
        'max_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'managed_users': len(users.list_users()),
        'note': 'Host read-only probes; CPU is collector CPU, RSS is collector peak. GTK activation and RDP load measured separately.',
    }
    print(json.dumps(result, indent=2))
