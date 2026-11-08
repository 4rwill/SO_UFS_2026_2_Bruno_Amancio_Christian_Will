import json
import tempfile
import unittest
from pathlib import Path

from genresearch.ingestion import generate


class CorpusTests(unittest.TestCase):
    def config(self, output, **changes):
        return dict(seed=202602, documents=12, sentences_per_document=24,
                    max_bytes=1048576, output=str(output), **changes)

    def test_reproducible_bytes_and_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            a, b = Path(temp) / "a", Path(temp) / "b"
            first, second = generate(self.config(a)), generate(self.config(b))
            self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])
            for file in a.iterdir():
                self.assertEqual(file.read_bytes(), (b / file.name).read_bytes())
            manifest = json.loads((a / "corpus.json").read_text())
            self.assertEqual(first["bytes"], sum(d["bytes"] for d in manifest["documents"]))

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "corpus"
            generate(self.config(output))
            before = (output / "corpus.json").read_bytes()
            with self.assertRaises(FileExistsError):
                generate(self.config(output))
            self.assertEqual(before, (output / "corpus.json").read_bytes())

    def test_limit_leaves_no_partial_corpus(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "corpus"
            config = self.config(output)
            config["max_bytes"] = 1
            with self.assertRaises(ValueError):
                generate(config)
            self.assertFalse(output.exists())
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_invalid_parameters(self):
        for key, value in [("documents", 0), ("documents", True),
                           ("sentences_per_document", 1001), ("max_bytes", 8388609)]:
            config = self.config("unused")
            config[key] = value
            with self.assertRaises(ValueError):
                generate(config)


if __name__ == "__main__":
    unittest.main()
