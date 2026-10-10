import unittest
from experiments.run_matrix import plan_queries
from experiments.analyze import describe


class MatrixTests(unittest.TestCase):
    def test_fixed_workload_has_distinct_and_repeated_queries(self):
        queries = plan_queries(202602, 24)
        self.assertEqual(queries, plan_queries(202602, 24))
        self.assertEqual(len(queries), 24)
        self.assertEqual(len(set(queries)), 9)
        self.assertNotEqual(queries, plan_queries(1, 24))

    def test_known_aggregation_and_missing_values(self):
        result = describe([1, None, 2, 3])
        self.assertEqual((result["n"], result["mean"], result["sd"]), (3, 2, 1))
        self.assertIsNone(describe([None])["mean"])
        self.assertIsNone(describe([1])["sd"])
