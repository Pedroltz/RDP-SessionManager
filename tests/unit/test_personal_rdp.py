import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from rdp_session_manager.infrastructure.user_manager import UserManager


class TestPersonalRDPUserManager(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.root = Path(self.tmpdir.name)
        self.rdp_home = self.root / "opt-rdp-users"
        self.rdp_home.mkdir()

        with patch.object(UserManager, "_ensure_base_setup"):
            self.manager = UserManager(rdp_users_home=str(self.rdp_home))
        self.manager.states_cache_file = self.root / "user_states.json"
        self.manager.personal_users_file = self.root / "personal_rdp_users.json"
        UserManager._user_states_cache = {}
        self.manager._persisted_states = {}

        self.personal_home = self.root / "home" / "alice"
        self.personal_home.mkdir(parents=True)
        self.fake_pwd = SimpleNamespace(
            pw_name="alice",
            pw_uid=1000,
            pw_gid=1000,
            pw_dir=str(self.personal_home),
        )

    def test_enable_personal_rdp_calls_manage_script_and_records_state(self):
        ok_proc = SimpleNamespace(returncode=0, stdout="OK", stderr="")
        expected_user = MagicMock()

        with (
            patch("pwd.getpwnam", return_value=self.fake_pwd),
            patch("rdp_session_manager.infrastructure.user_manager.get_privilege_command", return_value=("sudo", ["sudo"])),
            patch("rdp_session_manager.infrastructure.user_manager.run_command", return_value=ok_proc) as run_mock,
            patch.object(self.manager, "get_user", return_value=expected_user),
        ):
            result = self.manager.enable_personal_rdp("alice", desktop_env="xfce")

        self.assertIs(result, expected_user)
        cmd = run_mock.call_args[0][0]
        self.assertTrue(cmd[1].endswith("manage-personal-rdp.sh"))
        self.assertEqual(cmd[2:4], ["alice", "enable"])
        self.assertTrue(self.manager._load_personal_users().get("alice"))

    def test_lock_and_unlock_personal_user_never_lock_os_account_or_kill_processes(self):
        ok_proc = SimpleNamespace(returncode=0, stdout="OK", stderr="")
        with (
            patch("pwd.getpwnam", return_value=self.fake_pwd),
            patch("rdp_session_manager.infrastructure.user_manager.get_privilege_command", return_value=("sudo", ["sudo"])),
            patch("rdp_session_manager.infrastructure.user_manager.run_command", return_value=ok_proc) as run_mock,
            patch.object(self.manager, "kill_user_processes") as kill_mock,
        ):
            self.assertTrue(self.manager.lock_user("alice", kill_sessions=True))
            disable_cmd = run_mock.call_args[0][0]
            self.assertTrue(disable_cmd[1].endswith("manage-personal-rdp.sh"))
            self.assertEqual(disable_cmd[2:4], ["alice", "disable"])
            kill_mock.assert_not_called()
            self.assertFalse(self.manager._load_personal_users().get("alice"))

            self.assertTrue(self.manager.unlock_user("alice"))
            enable_cmd = run_mock.call_args[0][0]
            self.assertTrue(enable_cmd[1].endswith("manage-personal-rdp.sh"))
            self.assertEqual(enable_cmd[2:4], ["alice", "enable"])
            self.assertTrue(self.manager._load_personal_users().get("alice"))

    def test_delete_personal_user_never_calls_delete_rdp_user_script(self):
        self.manager._save_personal_user("alice", True)
        ok_proc = SimpleNamespace(returncode=0, stdout="OK", stderr="")

        with (
            patch("pwd.getpwnam", return_value=self.fake_pwd),
            patch.object(self.manager, "user_exists", return_value=True),
            patch("rdp_session_manager.infrastructure.user_manager.get_privilege_command", return_value=("sudo", ["sudo"])),
            patch("rdp_session_manager.infrastructure.user_manager.run_command", return_value=ok_proc) as run_mock,
        ):
            self.assertTrue(self.manager.delete_user("alice", remove_home=True, kill_processes=True))

        cmd = run_mock.call_args[0][0]
        self.assertTrue(cmd[1].endswith("manage-personal-rdp.sh"))
        self.assertEqual(cmd[2:4], ["alice", "remove"])
        self.assertNotIn("alice", self.manager._load_personal_users())

    def test_list_users_includes_disabled_personal_user(self):
        self.manager._save_personal_user("alice", False)
        empty_group = SimpleNamespace(gr_gid=9999, gr_mem=[])

        with (
            patch("grp.getgrnam", return_value=empty_group),
            patch("pwd.getpwall", return_value=[]),
            patch("pwd.getpwnam", return_value=self.fake_pwd),
            patch.object(self.manager, "_detect_session_info", return_value=("desktop", "xfce", "")),
            patch.object(self.manager, "is_superuser", return_value=False),
            patch.object(self.manager, "load_profiles_for_user", return_value=[]),
        ):
            users = self.manager.list_users()

        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].username, "alice")
        self.assertFalse(users[0].enabled)
        self.assertTrue(users[0].is_personal)
