"""Dados alterados aqui são fixtures em temporários, nunca medições publicadas."""
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit import audit, read
from lab import save


class AuditTests(unittest.TestCase):
    def setUp(self):
        batches = [p for p in (ROOT / 'results' / 'raw').iterdir()
                   if (p / 'manifest.json').exists() and read(p / 'manifest.json').get('status') == 'completed']
        if not batches:
            self.skipTest('Nenhuma evidência real disponível')
        temporary_root = ROOT / '.build' / 'test-temp'
        temporary_root.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=temporary_root)
        def cleanup():
            if not Path(self.temporary.name).resolve().is_relative_to(temporary_root.resolve()):
                raise ValueError('Destino de limpeza fora dos temporários de teste')
            self.temporary.cleanup()
        self.addCleanup(cleanup)
        self.batch = Path(self.temporary.name) / 'fixture'
        shutil.copytree(sorted(batches)[-1], self.batch)

    def rehash_fixture(self):
        save(self.batch / 'SHA256SUMS.json',
             {str(p.relative_to(self.batch)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in self.batch.rglob('*') if p.is_file() and p.name != 'SHA256SUMS.json'})

    def test_real_batch_passes(self):
        result, _ = audit(self.batch)
        self.assertEqual(result['main_runs'], 6)

    def test_corrupt_file_rejected(self):
        with (self.batch / 'runs' / 'C1-1.json').open('a') as stream:
            stream.write(' ')
        with self.assertRaisesRegex(ValueError, 'Hash divergente'):
            audit(self.batch)

    def test_wrong_checksum_rejected_even_with_recomputed_inventory(self):
        path = self.batch / 'runs' / 'C1-1.json'
        record = read(path)
        record['workload']['checksum'] += 1
        save(path, record)
        self.rehash_fixture()
        with self.assertRaisesRegex(ValueError, 'Checksum'):
            audit(self.batch)

    def test_requested_quota_does_not_replace_kernel_evidence(self):
        path = self.batch / 'runs' / 'C1-1.json'
        record = read(path)
        record['workload']['cgroup_after']['cpu.max'] = 'max 100000'
        save(path, record)
        self.rehash_fixture()
        with self.assertRaisesRegex(ValueError, 'Limites efetivos'):
            audit(self.batch)


if __name__ == '__main__':
    unittest.main()
