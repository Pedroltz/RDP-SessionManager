import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from rdp_session_manager.infrastructure import live_desktop
from rdp_session_manager.infrastructure.user_manager import UserManager


class TestLiveDesktopDetection(unittest.TestCase):
    def test_detects_gnome_wayland(self):
        info = live_desktop.detect_live_session_backend(
            {"XDG_SESSION_TYPE": "wayland", "XDG_CURRENT_DESKTOP": "GNOME"}
        )
        self.assertEqual(info["backend"], "gnome-remote-desktop")
        self.assertEqual(info["binary"], "grdctl")

    def test_detects_kde_wayland(self):
        info = live_desktop.detect_live_session_backend(
            {"XDG_SESSION_TYPE": "wayland", "XDG_CURRENT_DESKTOP": "KDE"}
        )
        self.assertEqual(info["backend"], "krdp")

    def test_detects_wlroots_wayland(self):
        info = live_desktop.detect_live_session_backend(
            {"XDG_SESSION_TYPE": "wayland", "XDG_CURRENT_DESKTOP": "Hyprland"}
        )
        self.assertEqual(info["backend"], "wayvnc")

    def test_detects_x11_shadow_fallback(self):
        info = live_desktop.detect_live_session_backend(
            {"XDG_SESSION_TYPE": "x11", "XDG_CURRENT_DESKTOP": "XFCE"}
        )
        self.assertEqual(info["backend"], "freerdp-shadow")


class TestLivePersonalRDPUserManager(unittest.TestCase):
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

    def test_legacy_boolean_personal_file_normalizes(self):
        self.manager.personal_users_file.write_text(json.dumps({"alice": False}), encoding="utf-8")
        loaded = self.manager._load_personal_users()
        self.assertEqual(loaded["alice"]["mode"], "xrdp")
        self.assertFalse(loaded["alice"]["enabled"])

    def test_enable_disable_and_remove_live_personal_rdp(self):
        expected_user = MagicMock()
        with (
            patch("pwd.getpwnam", return_value=self.fake_pwd),
            patch("rdp_session_manager.infrastructure.live_desktop.detect_live_session_backend", return_value={"backend": "gnome-remote-desktop"}),
            patch("rdp_session_manager.infrastructure.live_desktop.is_backend_installed", return_value=True),
            patch("rdp_session_manager.infrastructure.live_desktop.start_live_rdp", return_value=True) as start_mock,
            patch("rdp_session_manager.infrastructure.live_desktop.stop_live_rdp", return_value=True) as stop_mock,
            patch.object(self.manager, "get_user", return_value=expected_user),
        ):
            res = self.manager.enable_personal_rdp("alice", mode="live", port=3390, password="secret")
            self.assertIs(res, expected_user)
            start_mock.assert_called_once_with("alice", port=3390, password="secret", backend="gnome-remote-desktop")

            self.assertTrue(self.manager.lock_user("alice"))
            stop_mock.assert_called_with("gnome-remote-desktop")
            self.assertFalse(self.manager._load_personal_users()["alice"]["enabled"])

            self.assertTrue(self.manager.unlock_user("alice"))
            self.assertTrue(self.manager._load_personal_users()["alice"]["enabled"])

            with patch.object(self.manager, "user_exists", return_value=True):
                self.assertTrue(self.manager.delete_user("alice"))
            self.assertNotIn("alice", self.manager._load_personal_users())

class TestLiveFirewall(unittest.TestCase):
    @patch.object(live_desktop.shutil, 'which', return_value='/usr/bin/ufw')
    @patch.object(live_desktop, 'get_privilege_command', return_value=(True, ['pkexec']))
    @patch.object(live_desktop, 'run_command')
    def test_limits_rule_to_default_network(self, run, privilege, which):
        run.side_effect = [
            SimpleNamespace(returncode=0, stdout='Status: active'),
            SimpleNamespace(returncode=0, stdout=json.dumps([
                {'dst': 'default', 'dev': 'wlan0'},
                {'dst': '10.1.2.0/24', 'dev': 'wlan0', 'scope': 'link'},
                {'dst': '172.17.0.0/16', 'dev': 'docker0', 'scope': 'link'}])),
            SimpleNamespace(returncode=0)]
        self.assertTrue(live_desktop.ensure_live_firewall(3390))
        self.assertEqual(run.call_args.args[0], ['pkexec', 'ufw', 'allow', 'in', 'on',
            'wlan0', 'from', '10.1.2.0/24', 'to', 'any', 'port', '3390', 'proto', 'tcp'])
