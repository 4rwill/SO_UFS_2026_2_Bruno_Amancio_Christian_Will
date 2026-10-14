# GenResearch-Servidor — Sistemas Operacionais AV2 (2026.2)

Implementação e avaliação de um pipeline inspirado em recuperação aumentada por geração (RAG), com documentos sintéticos, vetores lexicais por hashing, recuperação top-k, fila limitada, cache LRU compartilhado e logs concorrentes.

A resposta usa `sleep` como simulação de espera: não há inferência de LLM, pesos de modelos ou uso de GPU. A interface é de terminal; `serve` executa uma carga finita local, sem HTTP.

## Artefatos para avaliação

| Item | Localização |
|---|---|
| Relatório — fonte LaTeX com gráficos incorporados | [deliverables/relatorio.tex](deliverables/relatorio.tex) |
| Responsabilidades da equipe | [docs/contributions.md](docs/contributions.md) |
| Vídeo e situação dos artefatos finais | [VIDEO.md](VIDEO.md) |
| Código e testes | `src/genresearch/` e `tests/` |
| Configurações e execução dos experimentos | `experiments/configs/` e [docs/experiments.md](docs/experiments.md) |
| Resultados brutos e evidências | [results/README.md](results/README.md) |
| Tabela de resultados | [results/analysis/matrix-15c7fb31/table.md](results/analysis/matrix-15c7fb31/table.md) |
| Gráficos PNG/SVG | [results/analysis/matrix-15c7fb31/figures/](results/analysis/matrix-15c7fb31/figures/) |
| Interpretação e limitações | [docs/analysis.md](docs/analysis.md) |
| Ambiente Linux | [docs/environment.md](docs/environment.md) |
| Arquitetura, fila/cache e sincronização | [architecture](docs/architecture.md), [concurrency](docs/concurrency.md), [synchronization](docs/synchronization.md) |
| Memória e definições das métricas | [docs/methodology.md](docs/methodology.md) |
| Processos, threads e chamadas de sistema | [docs/evidence.md](docs/evidence.md) |

## Execução no Linux

Requer Python >=3.10, `venv` e Bash. As medições publicadas usaram Python 3.14.4 em Ubuntu/WSL 2. A aplicação usa somente a biblioteca padrão e pode ser executada por `PYTHONPATH`, sem instalação do pacote. Para a matriz/coleta: `procps`, `sysstat`, `strace`, GNU `time` e Git. Em Ubuntu, as ferramentas podem ser instaladas com `sudo apt install python3-venv procps sysstat strace time git`.

Na raiz de um clone do repositório:

```bash
python3 -m venv .venv
source .venv/bin/activate
export PYTHONPATH=src:.
python -m unittest discover -s tests -v

python -m genresearch generate-corpus --config experiments/configs/corpus-linux.json
python -m genresearch ingest --config experiments/configs/baseline.json
python -m genresearch query --text "memoria pagina swap" --config experiments/configs/baseline.json --read-mode read
python -m genresearch query --text "memoria pagina swap" --config experiments/configs/baseline.json --read-mode mmap
python -m genresearch serve --config experiments/configs/concurrent.json
timeout 15 python experiments/demonstrate_race.py
```

Gerar corpus e ingerir são operações de preparação: recusam destinos existentes. Em uma segunda preparação, escolher destinos novos nos campos `output`, `corpus` e `index` das configurações correspondentes. Consulta, serviço e demonstração criam novos diretórios UUID para os resultados. `data/generated/` é recriável e não está versionado.

O preset `concurrent.json` usa 12 consultas, dois produtores, dois consumidores, fila quatro e cache três. Não equivale à matriz de desempenho, que usa 24 consultas por repetição. Os presets de consulta inválida e saturação retornam código 2 quando registram falhas/recusas explícitas; isso faz parte da validação de robustez.

## Auditar os resultados publicados

Os comandos abaixo conferem dados existentes, sem refazer as medições. Executar na raiz do repositório, com o ambiente acima ativo:

```bash
python scripts/verify_matrix.py results/raw/matrix/15c7fb31a435409597342b40f0d70665
```

Para verificar também os gráficos e a proveniência, instalar as dependências de análise:

```bash
python -m pip install -r requirements-analysis-lock.txt
python scripts/verify_analysis.py results/analysis/matrix-15c7fb31
```

## Reexecutar a matriz e gerar a análise

A matriz exige Linux, pelo menos 1 GiB de `MemAvailable` e 256 MiB livres em disco. Cada processo tem limite de espaço virtual de 512 MiB, CPU de 30 s e watchdog de 45 s. Não há alteração de swap nem limpeza automática do cache de páginas.

```bash
timeout 950 python experiments/run_matrix.py --config experiments/configs/matrix.json --repetitions 3
```

O executor cria um lote com novo UUID e gera seus próprios corpus e índices. O manifesto e as saídas identificam esse lote; os caminhos do lote publicado abaixo não devem ser usados para representar uma nova medição.

Para recalcular tabelas e gráficos a partir do lote publicado, sem alterar suas saídas originais:

```bash
python -m pip install -r requirements-analysis-lock.txt
saida_analise="results/local-validation/analise-$(date +%Y%m%d-%H%M%S)"
python experiments/analyze.py --input results/raw/matrix/15c7fb31a435409597342b40f0d70665 --output "$saida_analise/tabelas"
python experiments/plot_results.py --input results/raw/matrix/15c7fb31a435409597342b40f0d70665 --race results/raw/stage4/7309c1af68234c8aa1f17d02d92f4737 --output "$saida_analise/graficos"
```

Coleta e auditoria de processos, threads e syscalls estão descritas em [docs/evidence.md](docs/evidence.md). As ferramentas de análise recusam sobrescrita; usar destinos novos.

## Resultados e alcance

Lote principal: `15c7fb31a435409597342b40f0d70665`, coletado em 10/10/2026, com 11 condições × 3 repetições. Foram 720 consultas concluídas e 72 falhas intencionais de índice ausente, sem perdas ou duplicações de IDs. A demonstração isolada reduziu de dois para um cálculo da mesma chave.

| Comparação | Resultado observado |
|---|---|
| read → mmap | Janela média 0,454 → 0,395 s; RSS semelhante |
| 1 → 2 → 4 consumidores | Vazão 26,93 → 52,90 → 74,03 req/s |
| Cache 0 → 1 → 3 | Hit rate 0 → 6,94 → 31,94% |
| Corpus 12 → 48 → 192 documentos | RSS máximo amostrado médio 34,29 → 42,48 → 53,83 MiB |

O recorte tem corpus pequeno, geração simulada, três repetições em ordem fixa, logging e cópias integrais. A execução usou `/mnt/c` no WSL/DrvFS. E/S física por processo estava indisponível (`null`); swap foi zero nas amostras, sem demonstração de thrashing. Os ganhos não representam inferência real ou paralelismo de bytecode limitado por CPU. Reprodução completa em clone limpo Linux ainda não foi confirmada.

## Entrega e atribuição

O fonte do relatório está incluído e utiliza pdfLaTeX. O PDF final, os slides e a URL do vídeo ainda precisam ser incorporados. O relatório contém campos para o commit final e o vídeo; este último deve constar também neste README e em `VIDEO.md`.

**URL do vídeo:** ainda não informada.

Houve assistência de IA (Codex) na implementação, documentação, auditoria e análise. As fontes técnicas e as limitações estão documentadas; a revisão e a responsabilidade acadêmica pertencem à equipe. A tabela de responsabilidades registra a divisão atribuída, sem presumir participação técnica não comprovada pelos registros.
