# GenResearch-Servidor — Sistemas Operacionais AV2

Comece pelo [roteiro de organização e estudo](docs/overview.md) para entender
o fluxo, localizar código/resultados e conferir o que ainda depende da equipe.
Seleção dos arquivos e cuidados de continuidade em [docs/github.md](docs/github.md).

Fundação da aplicação local para estudar memória, armazenamento, filas e
sincronização em um pipeline inspirado em RAG. A versão atual gera corpus
sintético e executa ingestão e consulta sequenciais com vetores simulados.
Fila limitada, cache compartilhado e carga concorrente local estão implementados.
A matriz experimental e a análise inicial estão concluídas, com dados reais.

Sem API, GPU, modelo real ou bibliotecas externas de execução. Python >=3.10;
validação realizada com Python 3.12.14 no Windows e 3.14.4 no Ubuntu/WSL 2.
Dependências de build ainda não foram testadas. Coleta Linux executada;
experimentos e gráficos disponíveis; entregas acadêmicas permanecem pendentes.

Na raiz do repositório, com Python disponível, estes comandos foram executados
usando o Python local do aplicativo e PYTHONPATH=src:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests -v
python -m genresearch generate-corpus --config experiments/configs/corpus.json
```

O executável `python` do PATH deste computador é um atalho indisponível. Na
verificação, foi usado o executável fornecido pelo aplicativo, registrado em
[docs/status.md](docs/status.md). Os comandos acima exigem Python instalado no PATH.

O gerador cria data/generated/small com documentos e corpus.json contendo temas,
consultas, tamanhos e checksums SHA-256. Não sobrescreve destino existente: para
uma nova geração, use outro output no JSON. Os testes comparam dois destinos
temporários e verificam limites sem depender do corpus previamente gerado.

O preset tem 12 documentos, 24 frases por documento, semente 202602 e limite de
1 MiB. Dados gerados são ignorados pelo Git. Consulte [data/README.md](data/README.md).

A etapa 1 foi verificada no Linux. Comandos reais e ambiente virtual estão em
[docs/status.md](docs/status.md). A coleta aceita destino novo e duração de 1 a
60 segundos. Evidências em results/evidence/stage1-environment; ambiente e
limitações WSL em [docs/environment.md](docs/environment.md).

C1–C6, corrida/correção e análise estão implementados. Relatório final, slides
e vídeo ainda estão pendentes.
O protocolo e conceitos de memória estão em [docs/methodology.md](docs/methodology.md).

Etapa 2: comandos executados no Ubuntu, na raiz do repositório, com timeout de 60 s:

```bash
export PYTHONPATH=src
timeout 60 /home/will/.venvs/genresearch/bin/python -m genresearch ingest --config experiments/configs/baseline.json
timeout 60 /home/will/.venvs/genresearch/bin/python -m genresearch query --text "memoria pagina swap" --config experiments/configs/baseline.json --read-mode read
timeout 60 /home/will/.venvs/genresearch/bin/python -m genresearch query --text "memoria pagina swap" --config experiments/configs/baseline.json --read-mode mmap
/home/will/.venvs/genresearch/bin/python -m unittest discover -s tests -v
/home/will/.venvs/genresearch/bin/python scripts/verify_stage2.py
```

O corpus small-linux deve existir. A ingestão recusa índice existente; para repetir
altere index em baseline.json. Consultas podem ser repetidas, pois cada execução
cria um diretório novo por UUID em results/raw/stage2. O script verify_stage2
confere as saídas CLI salvas em results/evidence/stage2-final, geradas nesta
validação; os testes reproduzem a equivalência independentemente dessas saídas.
Cada run contém manifest.json, requests.jsonl, resources.csv, events.jsonl e
summary.json. A resposta é simulada por espera sleep de 0,01 s, sem modelo real
nem promessa de carga CPU. Consulte [docs/architecture.md](docs/architecture.md).

Etapa 3: o comando abaixo foi executado no Ubuntu e verifica testes e três cargas
(normal, consulta inválida e saturação), com watchdogs e checagem dos artefatos:

```bash
GENRESEARCH_PYTHON=/home/will/.venvs/genresearch/bin/python bash scripts/validate_stage3.sh results/evidence/stage3-check
```

O destino já existe; para repetir use um diretório novo. O índice da etapa 2 é
pré-requisito. Para executar apenas a carga normal, comando também verificado:

```bash
PYTHONPATH=src timeout 30 /home/will/.venvs/genresearch/bin/python -m genresearch serve --config experiments/configs/concurrent.json
```

Presets concurrent-failure.json e concurrent-saturation.json preservam resultados
e retornam 2 ao registrar falhas/recusas; a carga normal retorna 0. Cada run salva
cinco artefatos em results/raw/stage3. Configuração, fórmulas, classificação de
hits/misses e limites estão em [docs/concurrency.md](docs/concurrency.md).
Etapa 4 concluída: demonstração isolada de duplicação e correção single-flight,
comandos executados no WSL:

```bash
export PYTHONPATH=src:.
timeout 15 /home/will/.venvs/genresearch/bin/python experiments/demonstrate_race.py
timeout 60 /home/will/.venvs/genresearch/bin/python -m unittest discover -s tests -v
```

Cada versão roda em processo filho com timeout e encerramento. A versão incorreta
é exclusiva da demonstração. Runs novos em results/raw/stage4 preservam eventos,
contagens, tempos e status. Resultado verificado: dois cálculos sem coordenação,
um com proteção; 17 testes passaram. Veja [docs/synchronization.md](docs/synchronization.md).
A matriz C1–C6 foi executada com três repetições e limites de processo;
plano e limitações em [docs/experiments.md](docs/experiments.md).

```bash
export PYTHONPATH=src:.
timeout 950 /home/will/.venvs/genresearch/bin/python experiments/run_matrix.py --config experiments/configs/matrix.json --repetitions 3
/home/will/.venvs/genresearch/bin/python scripts/verify_matrix.py results/raw/matrix/15c7fb31a435409597342b40f0d70665
/home/will/.venvs/genresearch/bin/python experiments/analyze.py --input results/raw/matrix/15c7fb31a435409597342b40f0d70665 --output results/summary/matrix-15c7fb31
```

Comandos executados no WSL. Runner cria lote UUID novo; análise exige saída nova.
Dados finais em results/raw/matrix/15c7fb31a435409597342b40f0d70665; tabelas
derivadas em results/summary/matrix-15c7fb31. E/S por processo indisponível=null.
Gráficos e interpretação disponíveis em [docs/analysis.md](docs/analysis.md).
Cinco gráficos PNG/SVG, tabelas, diagnóstico e proveniência em
results/analysis/matrix-15c7fb31. Geração e verificação foram executadas no WSL:

```bash
PYTHONPATH=src:. /home/will/.venvs/genresearch/bin/python experiments/plot_results.py --input results/raw/matrix/15c7fb31a435409597342b40f0d70665 --race results/raw/stage4/7309c1af68234c8aa1f17d02d92f4737 --output results/analysis/matrix-15c7fb31
/home/will/.venvs/genresearch/bin/python scripts/verify_analysis.py results/analysis/matrix-15c7fb31
```

Para regenerar, escolha saída nova. Matplotlib 3.10.8 instalado apenas para
análise; versões testadas em requirements-analysis-lock.txt. A aplicação de
medição continua usando biblioteca padrão. Entregas acadêmicas permanecem pendentes.

Evidências complementares Linux concluídas: ps, /proc, strace, GNU time,
vmstat e iostat. Duas cargas instrumentadas com 24 consultas cada terminaram
corretamente; seis threads observadas por processo. Interpretação e limitações
em [docs/evidence.md](docs/evidence.md). Comandos executados no Ubuntu:

```bash
PYTHONPATH=src:. timeout 90 /home/will/.venvs/genresearch/bin/python scripts/collect_evidence.py --output results/evidence/linux-tracing-20261010
/home/will/.venvs/genresearch/bin/python scripts/verify_evidence.py results/evidence/linux-tracing-20261010 results/summary/linux-tracing-20261010-verified
```

Para repetir, escolher destinos novos. Exige índice da etapa 2 e ferramentas
Linux indicadas no guia de evidências. Dados brutos preservados e 51 hashes
auditados; traces separados da matriz de desempenho. E/S física por processo
continua indisponível no WSL. Relatório e slides adiados a pedido da equipe.
