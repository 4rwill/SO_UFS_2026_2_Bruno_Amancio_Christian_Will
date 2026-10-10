import json
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from genresearch.cache import SharedCache
from genresearch.ingestion import generate
from genresearch.pipeline import ingest
from genresearch.server import serve


class CacheTests(unittest.TestCase):
    def test_eviction_and_disabled(self):
        cache = SharedCache(1)
        self.assertEqual(cache.get_or_compute("a", lambda: {"x": 1}, 1)[1], "miss")
        value, state = cache.get_or_compute("a", lambda: self.fail("recomputed"), 1)
        value["x"] = 9
        self.assertEqual(state, "hit")
        self.assertEqual(cache.get_or_compute("a", lambda: None, 1)[0]["x"], 1)
        cache.get_or_compute("b", lambda: {"x": 2}, 1)
        self.assertEqual(cache.stats()["evictions"], 1)
        disabled = SharedCache(0)
        for _ in range(2):
            self.assertEqual(disabled.get_or_compute("a", lambda: 1, 1)[1], "miss")
        self.assertEqual(disabled.stats()["size"], 0)

    def test_single_flight_error_and_retry(self):
        cache = SharedCache(2)
        entered, release = threading.Event(), threading.Event()
        def compute():
            entered.set()
            if not release.wait(2):
                raise TimeoutError("test barrier")
            raise ValueError("controlled")
        with ThreadPoolExecutor(2) as executor:
            owner = executor.submit(cache.get_or_compute, "a", compute, 2)
            self.assertTrue(entered.wait(1))
            follower = executor.submit(cache.get_or_compute, "a", lambda: self.fail("duplicate"), 2)
            deadline = time.monotonic() + 1
            while cache.stats()["coalesced"] == 0 and time.monotonic() < deadline:
                time.sleep(.001)
            release.set()
            for future in (owner, follower):
                with self.assertRaises(ValueError):
                    future.result(timeout=2)
        self.assertEqual(cache.get_or_compute("a", lambda: 3, 1), (3, "miss"))


class ServerTests(unittest.TestCase):
    def config(self, root):
        config = json.loads(Path("experiments/configs/concurrent.json").read_text())
        config.update(corpus=str(root / "corpus"), index=str(root / "index"), results=str(root / "runs"))
        generate(dict(seed=1, documents=3, sentences_per_document=5, max_bytes=10000, output=config["corpus"]))
        ingest(config)
        return config

    def inspect(self, result):
        root = Path(result["artifacts"])
        records = [json.loads(line) for line in (root / "requests.jsonl").read_text().splitlines()]
        events = [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]
        self.assertEqual(len({r["request_id"] for r in records}), result["submitted"])
        self.assertEqual(len(records), result["submitted"])
        self.assertEqual([e["sequence"] for e in events], list(range(1, len(events) + 1)))
        self.assertEqual(sum(e["event"] == "request_final" for e in events), result["submitted"])
        self.assertEqual(result["lost"], 0)
        self.assertEqual(result["duplicates"], 0)
        self.assertEqual(result["worker_threads_alive"], 0)
        self.assertEqual(result["queue_size"], 0)
        return records

    def test_two_producers_two_consumers(self):
        with tempfile.TemporaryDirectory() as temp:
            config = self.config(Path(temp))
            result = serve(config)
            records = self.inspect(result)
            self.assertEqual(result["completed"], len(config["queries"]))
            self.assertLessEqual(result["queue_max"], config["queue_capacity"])
            self.assertTrue(all(r["queue_wait_s"] >= 0 for r in records))
            self.assertGreater(result["cache"]["hits"], 0)
            self.assertEqual({r["worker"] for r in records}, {0, 1})
            self.assertEqual({r["producer"] for r in records}, {0, 1})

    def test_failure_then_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            config = self.config(Path(temp))
            config["queries"] = ["", "memoria", "disco"]
            result = serve(config)
            self.inspect(result)
            self.assertEqual((result["failed"], result["completed"]), (1, 2))
            corpus = Path(config["index"]) / "corpus.bin"
            content = corpus.read_bytes()
            corpus.unlink()
            config["cache_capacity"] = 0
            result = serve(config)
            self.inspect(result)
            self.assertEqual(result["failed"], 3)
            corpus.write_bytes(content)
            config["queries"] = ["memoria", "disco"]
            result = serve(config)
            self.inspect(result)
            self.assertEqual(result["completed"], 2)

    def test_saturation_and_deadline(self):
        with tempfile.TemporaryDirectory() as temp:
            config = self.config(Path(temp))
            config.update(workers=1, queue_capacity=1, enqueue_timeout_s=.001,
                          cache_capacity=0, queries=["memoria"] * 30)
            original_query = __import__("genresearch.server", fromlist=["query"]).query
            def slow(*args):
                time.sleep(.05)
                return original_query(*args)
            with patch("genresearch.server.query", slow):
                result = serve(config)
            self.inspect(result)
            self.assertGreater(result["rejected"], 0)
            config["run_timeout_s"] = .001
            result = serve(config)
            self.inspect(result)
            self.assertGreater(result["failed"] + result["rejected"], 0)


if __name__ == "__main__":
    unittest.main()
