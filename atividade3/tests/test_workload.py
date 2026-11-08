"""Verifica o oráculo independente e rejeição de limites ausentes/incorretos."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from common import expected_checksum, limit_errors


class WorkloadTests(unittest.TestCase):
    def test_closed_form_matches_small_and_overflowing_loops(self):
        for n in (0, 1, 2, 37, 1000, 10000):
            self.assertEqual(expected_checksum(n), sum(i * i + 3 * i + 7 for i in range(n)) % (2 ** 32))

    def test_missing_or_wrong_limit_rejected(self):
        good = {'cpu.max': '50000 100000', 'cpu.stat': {'usage_usec': 1},
                'memory.max': '268435456', 'memory.swap.max': '0', 'pids.max': '64'}
        self.assertEqual(limit_errors(good, .5), [])
        for field in good:
            bad = dict(good)
            bad[field] = None
            self.assertTrue(limit_errors(bad, .5), field)
        self.assertTrue(limit_errors(good, 1))
        self.assertTrue(limit_errors(dict(good, **{'memory.swap.max': 'max'}), .5))
        self.assertTrue(limit_errors(dict(good, **{'cpu.max': 'max 100000'}), .5))


if __name__ == '__main__':
    unittest.main()
