import json
import multiprocessing
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from rdp_session_manager.infrastructure.persistence import atomic_write, UserStateRepository
from rdp_session_manager.infrastructure.user_profiles import ProfileRepository
from rdp_session_manager.infrastructure.commands import run_command
from rdp_session_manager.infrastructure.windows_app import _atomic_json
from rdp_session_manager.domain.users import ConnectionProfile


def update_state(path, username):
    UserStateRepository(path).update({username: False})


class PersistenceTest(unittest.TestCase):
    def test_failed_replace_preserves_old_content_and_removes_temporary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'states.json'
            path.write_text('{"existing": true}')
            with patch('os.replace', side_effect=OSError('disk error')):
                with self.assertRaises(OSError):
                    atomic_write(path, '{}')
            self.assertEqual(json.loads(path.read_text()), {'existing': True})
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_concurrent_processes_merge_changes_and_use_private_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'states.json'
            UserStateRepository(path).update({'existing': True})
            processes = [multiprocessing.Process(target=update_state, args=(path, f'user{i}')) for i in range(8)]
            for process in processes:
                process.start()
            for process in processes:
                process.join(5)
                self.assertEqual(process.exitcode, 0)
            self.assertEqual(len(UserStateRepository(path).load()), 9)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            UserStateRepository(path).update({}, ['existing'])
            self.assertNotIn('existing', UserStateRepository(path).load())

    def test_corrupt_state_is_recoverable_and_rejects_non_boolean_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'states.json'
            for payload in ('{broken', '[]', '{"alice": "false"}'):
                path.write_text(payload)
                self.assertEqual(UserStateRepository(path).load(), {})
            UserStateRepository(path).update({'alice': False})
            self.assertEqual(UserStateRepository(path).load(), {'alice': False})

    def test_profile_timeout_removes_staging_file(self):
        temporary = []
        def timeout(command, **_kwargs):
            temporary.append(Path(command[-1]))
            self.assertTrue(temporary[0].is_file())
            raise subprocess.TimeoutExpired(command, 30)
        with patch('rdp_session_manager.infrastructure.user_profiles.get_privilege_command', return_value=('sudo', ['sudo'])), patch('subprocess.run', side_effect=timeout):
            self.assertFalse(ProfileRepository().save_profiles_for_user('alice', [ConnectionProfile('default', 'Desktop')]))
        self.assertFalse(temporary[0].exists())

    def test_windows_state_replacement_preserves_owner_and_private_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            path.write_text('{}')
            owner = path.stat()
            with patch('os.geteuid', return_value=0), patch('os.chown') as chown:
                _atomic_json(path, {'state': 'ready'})
            self.assertEqual(chown.call_args.args[1:], (owner.st_uid, owner.st_gid))
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(path.read_text()), {'state': 'ready'})

    def test_commands_require_timeout_and_argument_sequence(self):
        for command, options in [('echo unsafe', {}), (['echo'], {'timeout': None}), (['echo'], {'shell': True})]:
            with self.assertRaises(ValueError):
                run_command(command, **options)
