import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from rdp_session_manager.infrastructure.user_manager import UserManager

class PersonalHealthTests(unittest.TestCase):
    def test_registered_live_user_does_not_require_managed_home_or_group(self):
        with tempfile.TemporaryDirectory() as home:
            manager = object.__new__(UserManager)
            manager.rdp_users_home = Path('/opt/rdp-users')
            account = SimpleNamespace(pw_dir=home, pw_gid=1000)
            with patch('pwd.getpwnam', return_value=account), patch('grp.getgrnam', side_effect=KeyError), patch.object(manager, '_load_personal_users', return_value={'alice': {'mode':'live', 'enabled':True, 'backend':'gnome-remote-desktop'}}), patch.object(manager, 'get_user_processes', return_value=[]), patch('rdp_session_manager.infrastructure.live_desktop.is_live_rdp_running', return_value=True):
                result = manager.diagnose_user('alice')
            self.assertTrue(result['healthy'])
            self.assertEqual(result['issues'], [])
