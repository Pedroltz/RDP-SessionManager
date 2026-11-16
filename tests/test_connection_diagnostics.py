import unittest
from unittest.mock import patch
from types import SimpleNamespace
from rdp_session_manager.infrastructure.connection_diagnostics import connection_error, has_rdp_group, has_local_session

class ConnectionDiagnosticsTests(unittest.TestCase):
    def test_password_error_does_not_repeat_sensitive_output(self):
        message = connection_error('ERRCONNECT_LOGON_FAILURE secret-password')
        self.assertIn('sharing password', message)
        self.assertNotIn('secret-password', message)

    def test_group_error_is_specific_to_xrdp(self):
        self.assertIn('does not require', connection_error('user is not in rdp-users'))

    @patch('rdp_session_manager.infrastructure.connection_diagnostics.grp.getgrnam', side_effect=KeyError)
    def test_missing_group(self, lookup):
        self.assertFalse(has_rdp_group('alice'))

    @patch('rdp_session_manager.infrastructure.connection_diagnostics.run_command')
    def test_local_graphical_session(self, run):
        run.side_effect = [SimpleNamespace(stdout='3 1000 alice seat0'), SimpleNamespace(stdout='Remote=no\nType=wayland\nState=active')]
        self.assertTrue(has_local_session('alice'))

    def test_unreachable_service(self):
        self.assertIn('firewall', connection_error('ERRCONNECT_CONNECT_FAILED'))
