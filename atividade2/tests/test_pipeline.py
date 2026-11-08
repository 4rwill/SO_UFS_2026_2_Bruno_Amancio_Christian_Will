import json
import tempfile
import unittest
from pathlib import Path

from genresearch.ingestion import generate
from genresearch.pipeline import ingest, query
from genresearch.retrieval import chunks, vector


class PipelineTests(unittest.TestCase):
    def setup_corpus(self, directory):
        root = Path(directory)
        generate(dict(seed=1, documents=3, sentences_per_document=5,
                      max_bytes=10000, output=str(root / "corpus")))
        config = json.loads(Path("experiments/configs/baseline.json").read_text())
        config.update(corpus=str(root / "corpus"), index=str(root / "index"),
                      results=str(root / "runs"), generation_delay_s=0)
        return config

    def test_deterministic_index_and_modes(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.setup_corpus(directory)
            ingest(config)
            first = Path(config["index"])
            config["index"] = str(Path(directory) / "second")
            ingest(config)
            for file in first.iterdir():
                self.assertEqual(file.read_bytes(), (Path(config["index"]) / file.name).read_bytes())
            a = query(config, "memoria pagina swap")
            config["read_mode"] = "mmap"
            b = query(config, "memoria pagina swap")
            for name in ("chunks", "context", "response", "logical_bytes_read", "index_version"):
                self.assertEqual(a[name], b[name])
            self.assertLessEqual(a["context_bytes"], config["context_bytes"])

    def test_unicode_byte_limit(self):
        from genresearch.retrieval import retrieve
        rows = [{"id": 0, "document": "x", "start_char": 0,
                 "text": "á🙂á", "vector": vector("á🙂á", 8)}]
        for limit in range(1, 10):
            result = retrieve(rows, "á", 8, 1, limit)
            self.assertLessEqual(len(result["context"].encode()), limit)
            result["context"].encode().decode("utf-8")

    def test_fragmentation(self):
        self.assertEqual(list(chunks("abcdefg", 4, 1)), [(0, "abcd"), (3, "defg")])
        with self.assertRaises(ValueError):
            list(chunks("x", 4, 4))
        self.assertEqual(vector("memoria", 64), vector("MEMORIA", 64))

    def test_corruption_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.setup_corpus(directory)
            ingest(config)
            with self.assertRaises(FileExistsError):
                ingest(config)
            (Path(config["index"]) / "corpus.bin").write_bytes(b"broken")
            with self.assertRaises(ValueError):
                query(config, "memoria")

    def test_input_and_chunk_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.setup_corpus(directory)
            config["max_chunks"] = 1
            with self.assertRaises(ValueError):
                ingest(config)
            self.assertFalse(Path(config["index"]).exists())

    def test_failed_run_is_recorded(self):
        from genresearch.metrics import run
        with tempfile.TemporaryDirectory() as directory:
            config = self.setup_corpus(directory)
            with self.assertRaises(FileNotFoundError):
                run(config, "query", lambda: query(config, "memoria"))
            root = next(Path(config["results"]).iterdir())
            self.assertEqual(json.loads((root / "manifest.json").read_text())["status"], "failed")
            self.assertEqual(json.loads((root / "summary.json").read_text())["failed"], 1)
            self.assertTrue(json.loads((root / "requests.jsonl").read_text())["error"])
            for line in (root / "events.jsonl").read_text().splitlines():
                json.loads(line)


if __name__ == "__main__":
    unittest.main()
