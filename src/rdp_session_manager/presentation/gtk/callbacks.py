"""Own GTK sources and prevent callbacks from touching a closed window."""
from threading import RLock


class CallbackScope:
    def __init__(self, scheduler):
        self._scheduler = scheduler
        self._lock = RLock()
        self._sources = set()
        self._closed = False

    def _add(self, schedule, callback, *args):
        source = []
        def guarded():
            with self._lock:
                if self._closed:
                    return False
            keep = False
            try:
                keep = bool(callback(*args))
                return keep
            finally:
                if not keep:
                    with self._lock:
                        if source:
                            self._sources.discard(source[0])
        with self._lock:
            if self._closed:
                return 0
            identifier = schedule(guarded)
            source.append(identifier)
            self._sources.add(identifier)
            return identifier

    def idle_add(self, callback, *args):
        return self._add(self._scheduler.idle_add, callback, *args)

    def timeout_add(self, milliseconds, callback, *args):
        return self._add(lambda guarded: self._scheduler.timeout_add(milliseconds, guarded), callback, *args)

    def timeout_add_seconds(self, seconds, callback, *args):
        return self._add(lambda guarded: self._scheduler.timeout_add_seconds(seconds, guarded), callback, *args)

    def close(self):
        with self._lock:
            self._closed = True
            for source in self._sources:
                self._scheduler.source_remove(source)
            self._sources.clear()
