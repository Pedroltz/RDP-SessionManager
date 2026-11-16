"""Atomic settings replacement and locked merge of account state changes."""
import fcntl
import json
import logging
import os
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


def atomic_write(path: Path, content: str, mode=0o600):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', dir=path.parent, encoding='utf-8', delete=False) as stream:
            temporary = Path(stream.name)
            os.fchmod(stream.fileno(), mode)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class UserStateRepository:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        try:
            payload = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(payload, dict) or any(not isinstance(value, bool) for value in payload.values()):
                raise ValueError('Expected account names mapped to booleans')
            return payload
        except FileNotFoundError:
            return {}
        except (OSError, ValueError) as exc:
            logger.warning('Cannot load account states from %s: %s', self.path, exc)
            return {}

    def update(self, changes, removed=()):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_CREAT | os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0)
        descriptor = os.open(str(self.path) + '.lock', flags, 0o600)
        with os.fdopen(descriptor, 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            current = self.load()
            current.update(changes)
            for username in removed:
                current.pop(username, None)
            atomic_write(self.path, json.dumps(current, indent=2))
            return current
