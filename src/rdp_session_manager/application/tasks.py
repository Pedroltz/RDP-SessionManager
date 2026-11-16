"""Serialize background refreshes and discard results after shutdown."""
import logging
from threading import Lock, Thread
from rdp_session_manager.application.ports import Dispatcher

logger = logging.getLogger(__name__)


class BackgroundTasks:
    def __init__(self, dispatch: Dispatcher, thread_factory=Thread):
        self._dispatch = dispatch
        self._thread_factory = thread_factory
        self._lock = Lock()
        self._closed = False
        self._running = set()
        self._pending = {}

    def submit(self, key, work, done, *, coalesce=False):
        with self._lock:
            if self._closed:
                return False
            if key in self._running:
                if coalesce:
                    self._pending[key] = (work, done)
                return False
            self._running.add(key)

        def worker():
            value, error = None, None
            try:
                value = work()
            except Exception as exc:
                error = exc
                logger.warning('Background task %s failed: %s', key, exc)
            def deliver():
                with self._lock:
                    self._running.discard(key)
                    pending = self._pending.pop(key, None)
                    closed = self._closed
                if not closed:
                    try:
                        done(value, error)
                    finally:
                        if pending:
                            self.submit(key, *pending, coalesce=True)
                return False
            with self._lock:
                if self._closed:
                    self._running.discard(key)
                    return
            self._dispatch(deliver)

        try:
            self._thread_factory(target=worker, daemon=True).start()
        except Exception:
            with self._lock:
                self._running.discard(key)
            raise
        return True

    def close(self):
        with self._lock:
            self._closed = True
            self._pending.clear()
