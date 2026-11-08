// Compatibilidade com o comando antigo; as miniaturas vêm do PDF Beamer.
// Preferir: python atividade3/scripts/render_roteiros_slides.py
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
const python = process.env.CODEX_RUNTIME_PYTHON || 'python';
const script = path.join(path.dirname(fileURLToPath(import.meta.url)), 'render_roteiros_slides.py');
const result = spawnSync(python, [script, ...process.argv.slice(2)], {stdio:'inherit'});
if (result.error) throw result.error;
process.exitCode = result.status ?? 1;
