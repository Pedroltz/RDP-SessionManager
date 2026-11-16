"""Executable dependency boundaries and headless entry point contract."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'src/rdp_session_manager'


class ArchitectureTest(unittest.TestCase):
    def test_dependency_direction_and_no_internal_legacy_imports(self):
        for path in PACKAGE.rglob('*.py'):
            layer = path.relative_to(PACKAGE).parts[0]
            for node in ast.walk(ast.parse(path.read_text())):
                modules = ([node.module or ''] if isinstance(node, ast.ImportFrom)
                           else [item.name for item in node.names] if isinstance(node, ast.Import) else [])
                for module in modules:
                    with self.subTest(path=path, module=module):
                        self.assertNotIn(module.split('.')[0], {'core', 'ui', 'utils'})
                        if layer == 'domain':
                            self.assertNotIn(module.split('.')[0], {'gi','psutil','pwd','grp','subprocess','fcntl','socket'})
                            self.assertFalse(module.startswith(('rdp_session_manager.application', 'rdp_session_manager.infrastructure', 'rdp_session_manager.presentation', 'rdp_session_manager.bootstrap')))
                        elif layer == 'application':
                            self.assertFalse(module.startswith(('gi', 'rdp_session_manager.infrastructure', 'rdp_session_manager.presentation', 'rdp_session_manager.bootstrap')))
                        elif layer == 'infrastructure':
                            self.assertFalse(module.startswith('rdp_session_manager.presentation'))

    def test_cli_runs_with_gtk_import_forbidden(self):
        environment = dict(os.environ, PYTHONPATH=str(ROOT / 'src'))
        script = '''import sys
class NoGTK:
    def find_spec(self, fullname, *args):
        if fullname == 'gi' or fullname.startswith('gi.'):
            raise AssertionError('CLI imported GTK')
sys.meta_path.insert(0, NoGTK())
from rdp_session_manager.presentation.cli.commands import CLI
assert CLI().run(['--help']) == 0
assert 'gi' not in sys.modules
'''
        result = subprocess.run([sys.executable, '-c', script], env=environment, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_only_canonical_source_package_is_distributed(self):
        self.assertTrue((PACKAGE / '__init__.py').is_file())
        self.assertFalse((ROOT / 'rdp_session_manager').exists())
        for obsolete in ('core', 'ui', 'utils', 'main.py', 'cli.py', 'application.py', 'version.py'):
            self.assertFalse((ROOT / 'src' / obsolete).exists(), obsolete)

    def test_absolute_cli_entry_survives_missing_pythonpath(self):
        environment = dict(os.environ)
        environment.pop('PYTHONPATH', None)
        entry = PACKAGE / 'presentation/cli/__main__.py'
        result = subprocess.run([sys.executable, str(entry), '--help'], cwd='/tmp',
                                env=environment, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
