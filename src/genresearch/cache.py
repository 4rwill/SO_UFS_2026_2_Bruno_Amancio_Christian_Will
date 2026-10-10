"""LRU protegido com coordenação por chave; cálculo ocorre fora do lock."""
from collections import OrderedDict
from copy import deepcopy
from threading import Event, Lock


class SharedCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.lock = Lock()
        self.values = OrderedDict()
        self.pending = {}
        self.hits = self.misses = self.evictions = self.coalesced = 0

    def get_or_compute(self, key, compute, timeout):
        with self.lock:
            if self.capacity and key in self.values:
                self.hits += 1
                self.values.move_to_end(key)
                return deepcopy(self.values[key]), "hit"
            self.misses += 1
            flight = self.pending.get(key) if self.capacity else None
            owner = flight is None
            if owner:
                flight = {"done": Event(), "result": None, "error": None}
                if self.capacity:
                    self.pending[key] = flight
            else:
                self.coalesced += 1
        if not owner:
            if not flight["done"].wait(timeout):
                raise TimeoutError("Espera de cache excedeu timeout")
            if flight["error"] is not None:
                raise flight["error"]
            return deepcopy(flight["result"]), "coalesced"
        try:
            result = compute()
        except Exception as error:
            with self.lock:
                flight["error"] = error
                self.pending.pop(key, None)
                flight["done"].set()
            raise
        with self.lock:
            flight["result"] = result
            if self.capacity:
                self.values[key] = result
                if len(self.values) > self.capacity:
                    self.values.popitem(last=False)
                    self.evictions += 1
                self.pending.pop(key, None)
            flight["done"].set()
        return deepcopy(result), "miss"

    def stats(self):
        with self.lock:
            count = self.hits + self.misses
            return {"hits": self.hits, "misses": self.misses, "coalesced": self.coalesced,
                    "evictions": self.evictions, "size": len(self.values),
                    "hit_rate": self.hits / count if count else None,
                    "miss_rate": self.misses / count if count else None}
