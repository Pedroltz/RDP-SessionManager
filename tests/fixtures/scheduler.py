"""Deterministic thread and event-loop fixtures: no sleeps or GTK required."""
class DeferredThread:
    queue = []

    def __init__(self, target, daemon=False):
        self.target = target

    def start(self):
        self.queue.append(self.target)


class Scheduler:
    def __init__(self):
        self.callbacks = {}
        self.counter = 0
        self.removed = []

    def idle_add(self, callback):
        self.counter += 1
        self.callbacks[self.counter] = callback
        return self.counter

    def timeout_add(self, _delay, callback):
        return self.idle_add(callback)

    timeout_add_seconds = timeout_add

    def source_remove(self, identifier):
        self.removed.append(identifier)
        self.callbacks.pop(identifier, None)

    def drain(self):
        for identifier, callback in list(self.callbacks.items()):
            if not callback():
                self.callbacks.pop(identifier, None)
