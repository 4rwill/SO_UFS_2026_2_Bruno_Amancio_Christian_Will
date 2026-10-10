import json
import tempfile
import unittest
from pathlib import Path

from experiments.demonstrate_race import demonstrate, isolated


class RaceTests(unittest.TestCase):
    def test_duplicate_and_corrected_results(self):
        with tempfile.TemporaryDirectory() as temp:
            result = demonstrate(temp)
            self.assertTrue(result["passed"])
            a, b = result["comparisons"]
            self.assertEqual((a["calculations"], b["calculations"]), (2, 1))
            self.assertEqual(b["cache"]["coalesced"], 1)
            for mode in ("unsafe", "corrected"):
                events = [json.loads(line) for line in
                          (Path(result["artifacts"]) / f"{mode}-events.jsonl").read_text().splitlines()]
                if mode == "unsafe":
                    misses = [e["sequence"] for e in events if e["event"] == "observed_miss"]
                    calculations = [e["sequence"] for e in events if e["event"] == "compute_start"]
                    self.assertEqual(len(misses), 2)
                    self.assertLess(max(misses), min(calculations))
                self.assertEqual(events[-1]["worker_threads_alive"], 0)

    def test_parent_watchdog_terminates_child(self):
        with tempfile.TemporaryDirectory() as temp:
            result = isolated("corrected", temp, timeout=0)
            self.assertEqual(result["status"], "timeout")
            self.assertIsNone(result["calculations"])
            self.assertFalse(result["process_alive"])


if __name__ == "__main__":
    unittest.main()
