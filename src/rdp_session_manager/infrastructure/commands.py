"""Bounded, shell-free command execution; callers own domain error messages."""
import subprocess


def run_command(command, *, timeout=30, **kwargs):
    if timeout is None or timeout <= 0:
        raise ValueError('Commands require a positive timeout')
    if isinstance(command, (str, bytes)) or kwargs.get('shell'):
        raise ValueError('Pass an argument sequence without shell=True')
    return subprocess.run(command, timeout=timeout, **kwargs)
