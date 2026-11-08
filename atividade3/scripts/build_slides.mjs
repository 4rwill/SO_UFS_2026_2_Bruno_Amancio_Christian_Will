// Compatibilidade com o comando antigo. O fonte oficial agora é LaTeX Beamer.
// Preferir: python atividade3/scripts/build_slides.py
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
const python = process.env.CODEX_RUNTIME_PYTHON || 'python';
const script = path.join(path.dirname(fileURLToPath(import.meta.url)), 'build_slides.py');
const result = spawnSync(python, [script, ...process.argv.slice(2)], {stdio:'inherit'});
if (result.error) throw result.error;
process.exitCode = result.status ?? 1;
