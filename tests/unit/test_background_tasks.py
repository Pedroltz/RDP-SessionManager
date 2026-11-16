import sys
from pathlib import Path
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from fixtures.scheduler import DeferredThread, Scheduler
from rdp_session_manager.application.tasks import BackgroundTasks
from rdp_session_manager.presentation.gtk.callbacks import CallbackScope


class BackgroundTasksTest(unittest.TestCase):
    def setUp(self):
        DeferredThread.queue.clear()
        self.scheduler = Scheduler()
        self.scope = CallbackScope(self.scheduler)
        self.tasks = BackgroundTasks(self.scope.idle_add, DeferredThread)

    def test_refreshes_do_not_overlap_and_mutation_refresh_is_coalesced(self):
        first, latest, done = Mock(return_value=1), Mock(return_value=2), Mock()
        self.assertTrue(self.tasks.submit('users', first, done))
        self.assertFalse(self.tasks.submit('users', latest, done, coalesce=True))
        self.assertEqual(len(DeferredThread.queue), 1)
        DeferredThread.queue.pop(0)()
        self.scheduler.drain()
        done.assert_called_once_with(1, None)
        self.assertEqual(len(DeferredThread.queue), 1)
        DeferredThread.queue.pop(0)()
        self.scheduler.drain()
        self.assertEqual(done.call_args.args, (2, None))

    def test_close_drops_queued_completion_and_periodic_sources(self):
        done = Mock()
        self.scope.timeout_add_seconds(5, Mock(return_value=True))
        self.tasks.submit('health', lambda: 1, done)
        DeferredThread.queue.pop(0)()
        self.tasks.close()
        self.scope.close()
        self.scheduler.drain()
        done.assert_not_called()
        self.assertEqual(len(self.scheduler.removed), 2)
        self.assertFalse(self.tasks.submit('health', lambda: 2, done))
        self.assertEqual(self.scope.idle_add(done), 0)

    def test_close_during_worker_prevents_dispatch(self):
        done = Mock()
        def work():
            self.tasks.close()
            return 3
        self.tasks.submit('health', work, done)
        DeferredThread.queue.pop(0)()
        self.assertFalse(self.scheduler.callbacks)
        done.assert_not_called()

    def test_failed_query_delivers_error_and_can_retry(self):
        error, done = ValueError('offline'), Mock()
        def fail():
            raise error
        self.tasks.submit('users', fail, done)
        DeferredThread.queue.pop(0)()
        self.scheduler.drain()
        done.assert_called_once_with(None, error)
        self.assertTrue(self.tasks.submit('users', lambda: 1, done))
