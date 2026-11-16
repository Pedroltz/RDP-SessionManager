import sys
from pathlib import Path
from threading import Event, Thread
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from rdp_session_manager.application.dashboard import Dashboard
from rdp_session_manager.application.users import UserService
from rdp_session_manager.domain.users import RDPUser
from rdp_session_manager.domain.sessions import SessionInfo
from rdp_session_manager.infrastructure.session_monitor import SessionMonitor


class DashboardTest(unittest.TestCase):
    def test_one_snapshot_per_cycle_counts_only_enabled_users(self):
        users, sessions = Mock(), Mock()
        users.list_users.return_value = [RDPUser('enabled', 5000, '/tmp/a'), RDPUser('disabled', 5001, '/tmp/b', enabled=False)]
        sessions.get_active_sessions.return_value = [SessionInfo('enabled'), SessionInfo('disabled')]
        sessions.get_ip_address.return_value = '192.0.2.1'
        snapshot = Dashboard(users, sessions).collect()
        self.assertEqual(snapshot.enabled_session_count, 1)
        self.assertEqual(snapshot.active_usernames, {'enabled', 'disabled'})
        users.list_users.assert_called_once()
        sessions.get_active_sessions.assert_called_once()

    def test_mutation_invalidates_sessions_even_after_partial_failure(self):
        repository, sessions = Mock(), Mock()
        service = UserService(repository, sessions)
        repository.rename_user.side_effect = RuntimeError('profile failure')
        with self.assertRaises(RuntimeError):
            service.rename_user('before', 'after')
        sessions.invalidate.assert_called_once()

    def test_query_does_not_invalidate(self):
        repository, sessions = Mock(), Mock()
        service = UserService(repository, sessions)
        service.list_users()
        sessions.invalidate.assert_not_called()

    def test_overlapping_monitor_reads_share_a_scan_and_invalidation_refreshes(self):
        monitor = SessionMonitor(cache_ttl=60)
        entered, release = Event(), Event()
        def scan(_processes):
            entered.set()
            self.assertTrue(release.wait(2))
            return []
        with patch.object(monitor, '_get_rdp_connections', side_effect=scan) as query, patch('psutil.process_iter', return_value=[]) as processes:
            first = Thread(target=monitor.get_active_sessions)
            second = Thread(target=monitor.get_active_sessions)
            first.start()
            self.assertTrue(entered.wait(2))
            second.start()
            release.set()
            first.join(2)
            second.join(2)
            self.assertFalse(first.is_alive() or second.is_alive())
            self.assertEqual(query.call_count, 1)
            processes.assert_called_once()
            monitor.invalidate()
            monitor.get_active_sessions()
            self.assertEqual(query.call_count, 2)

    @patch('psutil.cpu_percent', return_value=0)
    def test_cpu_statistics_never_sleep(self, cpu):
        monitor = SessionMonitor()
        with patch.object(monitor, 'get_session_count', return_value=0):
            monitor.get_system_stats()
        cpu.assert_called_once_with(interval=None)
