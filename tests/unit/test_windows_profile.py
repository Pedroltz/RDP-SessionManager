import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from rdp_session_manager.domain.users import ConnectionProfile
from rdp_session_manager.application.windows_profiles import bind_windows_application


class WindowsProfileTest(unittest.TestCase):
    def test_native_profile_is_rebound_to_managed_launcher_and_survives_roundtrip(self):
        profile = ConnectionProfile('windows', 'Fixture', 'remoteapp', app_command='xfce4-terminal')
        bind_windows_application(profile, 'fixture', '/apps/fixture.exe', ['/usr/bin/python3','/helpers/launch-windows-app.py'])
        loaded = ConnectionProfile.from_dict(profile.to_dict())
        self.assertEqual(loaded.runtime, 'managed')
        self.assertEqual(loaded.resource_profile, 'windows-standard')
        self.assertEqual(loaded.command_argv, ['/usr/bin/python3','/helpers/launch-windows-app.py','fixture'])
        spec = importlib.util.spec_from_file_location('managed_session_test', ROOT/'helpers/rdpsm-session.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.runtime_argv(loaded.to_dict(), Path('/unused')), loaded.command_argv)
