/** Renderiza as miniaturas dos slides para os PDFs de falas.
 * Requer o Node.js e @oai/artifact-tool do runtime Codex.
 * Definir CODEX_RUNTIME_NODE_MODULES com o diretório de pacotes do runtime.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath, pathToFileURL} from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const packages = process.env.CODEX_RUNTIME_NODE_MODULES || process.env.RUNTIME_NODE_MODULES;
if (!packages) throw new Error('Definir CODEX_RUNTIME_NODE_MODULES com o caminho dos pacotes do runtime Codex.');
const {PresentationFile, FileBlob} = await import(pathToFileURL(path.join(packages, '@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const plan = JSON.parse(await fs.readFile(path.join(root, 'docs/roteiros_falas.json'), 'utf8'));
const source = path.resolve(root, '..', plan.deck);
const digest = createHash('sha256').update(await fs.readFile(source)).digest('hex');
if (digest !== plan.deck_sha256) throw new Error('Os slides mudaram; revisar o roteiro e o hash de referência.');
const deck = await PresentationFile.importPptx(await FileBlob.load(source));
if (deck.slides.items.length !== plan.slides.length) throw new Error('Quantidade de slides divergente do roteiro.');
const output = path.join(root, '.build/roteiros/slides');
await fs.mkdir(output, {recursive:true});
for (const [index, slide] of deck.slides.items.entries()) {
  const image = await deck.export({slide, format:'png', scale:1});
  await fs.writeFile(path.join(output, `slide-${String(index + 1).padStart(2, '0')}.png`), new Uint8Array(await image.arrayBuffer()));
}
console.log(`Renderizadas ${deck.slides.items.length} miniaturas em ${output}`);
