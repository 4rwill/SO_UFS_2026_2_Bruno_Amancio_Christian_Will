import threading
import time
from datetime import datetime, timezone

from .storage import encode


class EventLog:
    def __init__(self, path):
        self.stream = path.open("wb")
        self.lock = threading.Lock()
        self.sequence = 0

    def emit(self, event, **fields):
        with self.lock:
            self.sequence += 1
            record = dict(event=event, sequence=self.sequence, monotonic_s=time.monotonic(),
                          timestamp=datetime.now(timezone.utc).isoformat(), **fields)
            self.stream.write(encode(record))
            self.stream.flush()

    def close(self):
        self.stream.close()
