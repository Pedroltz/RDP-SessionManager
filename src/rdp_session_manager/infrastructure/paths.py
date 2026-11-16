"""Resolve resources for a checkout, distro installation, or Python wheel."""
from pathlib import Path
import sys


def resource_root() -> Path:
    checkout = Path(__file__).resolve().parents[3]
    if (checkout / 'helpers').is_dir() and (checkout / 'data/ui').is_dir():
        return checkout
    return Path(sys.prefix) / 'share/rdp-session-manager'


def helper_dir() -> Path:
    return resource_root() / 'helpers'


def ui_file(name: str) -> Path:
    return resource_root() / 'data/ui' / name


def recipe_directories():
    root = resource_root()
    return (root / 'data/windows-app-recipes', root / 'windows-app-recipes')


def cli_command() -> list[str]:
    """Absolute entry point survives privilege elevation stripping PYTHONPATH."""
    entry = Path(__file__).resolve().parents[1] / 'presentation/cli/__main__.py'
    return [sys.executable, str(entry)]
