# Status — 10/10/2026 (America/Sao_Paulo)

## Etapa 1 — concluída

- [x] Inspecionar repositório e preservar arquivos da equipe.
- [x] Ler guia e texto das quatro páginas do PDF fornecido; Parte A compatível, WSL permitido.
- [x] Registrar distribuição, kernel, CPU/CPUs, RAM/swap, disco/FS, GPU/VRAM e isolamento.
- [x] Registrar linguagem, bibliotecas, ferramenta, commit/estado e data com fuso.
- [x] Coletar uname, os-release, lscpu, free, meminfo, lsblk, df e swapon.
- [x] Executar vmstat/iostat por 5 segundos com encerramento automático.
- [x] Explicar MemFree, MemAvailable, cache, swap e cache de páginas.
- [x] Preparar dependências, README e gerador reproduzível por CLI.
- [x] Verificar quatro testes e geração por CLI no Linux.

Evidências: results/evidence/stage1-environment e results/evidence/stage1-validation.
Todos os comandos da nova coleta retornaram 0, exceto vmstat/iostat: 124 pelo
encerramento previsto. Coletas parciais anteriores preservadas, sem edição dos dados.
Ambiente: docs/environment.md. Conceitos: docs/methodology.md.

## Implementado, verificado e executado

Gerador com semente, temas, consultas, bytes e SHA-256; recusa sobrescrita,
parâmetros inválidos e corpus parcial. Preset 1 MiB, teto 8 MiB, timeout 30 s,
reserva de disco de limite + 1 MiB. Quatro testes passaram no Windows Python
3.12.14 e Linux Python 3.14.4. CLI Linux gerou 12 documentos, 20.797 bytes;
manifesto igual ao Windows por cmp, SHA-256:
da5e86186ce467edb99cd82c22506f7e981904ae971a5cab239d622ef3574a00.

Instalados python3-venv, sysstat e pciutils; venv com pip criado no disco Linux.
Git funciona com safe.directory limitado à chamada e ao checkout, sem exceção
global. apt terminou com código 0, mas relatou falha do trigger systemd-binfmt;
não impediu os testes/coleta. Build/install via pip permanece não testado;
execução usa PYTHONPATH=src e biblioteca padrão.

## Comandos executados no Linux

```bash
python3 -m venv /home/will/.venvs/genresearch
cd /mnt/c/Projetos/SO_UFS_2026_2_Bruno_Amancio_Christian_Will
PYTHONPATH=src /home/will/.venvs/genresearch/bin/python -m unittest discover -s tests -v
PYTHONPATH=src /home/will/.venvs/genresearch/bin/python -m genresearch generate-corpus --config experiments/configs/corpus-linux.json
GENRESEARCH_PYTHON=/home/will/.venvs/genresearch/bin/python bash scripts/collect_environment.sh results/evidence/stage1-environment 5
cmp data/generated/small/corpus.json data/generated/small-linux/corpus.json
```

Destinos de geração/coleta já existem; para repetir use destinos novos.
Testes usam temporários e podem ser repetidos. Corpus gerado ignorado pelo Git.

## Pendente nas próximas etapas

- [x] Etapa 2: fragmentação, vetores, índice/metadados, top-k, contexto, resposta e métricas; read/mmap.
- [x] Etapa 3: fila 2 produtores/2 consumidores, cache protegido, logs, erros e encerramento.
- [x] Etapa 4: corrida isolada e correção single-flight com timeout.
- [x] C1–C4, C5 limitado/C6, três repetições válidas e três fatores.
- [x] Manifest, requests, resources, events, summary; métricas indisponíveis=null.
- [x] Análise, tabelas e gráficos dos resultados reais.
- [x] Evidências complementares de processos/threads/syscalls; limitações de E/S WSL registradas.
- [ ] Relatório 8–12 páginas, slides, vídeo e reprodução em clone limpo.

C1–C6 executados conforme registro da matriz abaixo, com C5 limitado.
Coleta de ambiente não é resultado de desempenho. Não limpar cache
nem alterar swap. Equipe deve confirmar integrantes/contribuições, nome público
do repositório, canal/fuso de entrega; supervisionar medições, vídeo e apresentação.

Fonte: PDF indicado pela equipe, texto consultado em 10/10/2026; sem divergência
na Parte A. Assistência Codex nesta etapa; nenhuma contribuição humana inferida.
Commit base e649deb2855910f8aa890bb6858d7fb744e5ce8c, alterações não commitadas.

## Etapa 2 — concluída, verificação Linux

Implementada ingestão com checksums, vetores SHA-256 normalizados, índice JSON e
corpus.bin. Consulta sequencial top-k com contexto limitado, resposta simulada
sleep e tempos de carregamento/recuperação/geração/total. CLI e documentação atualizados.
Cada execução salva cinco artefatos em results/raw/stage2, sem sobrescrever runs.

Dez testes passaram no WSL Python 3.14.4: determinismo, read/mmap, UTF-8/limite,
fragmentação, corrupção, recusa de sobrescrita, limite de fragmentos e registro
de falha, além dos quatro testes de corpus. Evidência final em
results/evidence/stage2-final/tests.txt. Ingestão e duas consultas CLI reais
executadas com timeout 60 s; resultados em ingest.json, read.json e mmap.json.
verify_stage2.py confirmou conteúdo, recuperação, resposta, bytes e versão de
índice idênticos, além de artefatos válidos (equivalence.txt).
Corpus: 20.797 bytes; índice: 75.314 bytes; 96 fragmentos. Metadados também
persistidos. Ensaios iniciais preservados em stage2-validation.

Limitações: validação funcional de uma consulta por modo, não três repetições de
C1/C2; recursos apenas antes/depois, sem pico; mmap copia os bytes; logs start/fim
sequenciais naquela etapa. Fila/cache e amostragem foram adicionados na etapa 3
abaixo; matriz permanece pendente. Nenhuma superioridade de read/mmap foi afirmada.
Reprodução e configuração: README.md, experiments/configs/baseline.json e
docs/architecture.md. Índice existente exige destino novo para nova ingestão;
consultas e testes podem ser repetidos.

## Etapa 3 — concluída, verificada no WSL

Implementados server.py, cache.py e logging_setup.py; CLI serve e presets de
carga normal, erro controlado e saturação. Fila limitada, LRU/single-flight,
logs protegidos, amostragem, métricas de fila/latência/vazão/cache/utilização,
falhas/recusas explícitas e protocolo de encerramento. Configuração e limites
em docs/concurrency.md; não há execução deliberadamente incorreta normal.

15 testes passaram no Python 3.14.4 Linux, incluindo recuperação após arquivo
ausente, saturação e prazo cooperativo. Evidência final: stage3-check/tests.txt.
CLI real: normal 12 concluídas; erro 3 concluídas/1 falha; saturação 3
concluídas/27 recusadas. Todos sem perdas/duplicações e sem threads de trabalho
vivas, fila final vazia. Logs parseáveis e ordem de eventos/IDs verificados por
scripts/verify_stage3.py (integrity.txt). Saídas CLI apontam runs imutáveis em
results/raw/stage3. Ensaios anteriores preservados; stage3-final inclui falha
do comando shell de conferência; stage3-check é a validação bem-sucedida.

Comando real executado, na raiz do projeto Linux:

```bash
GENRESEARCH_PYTHON=/home/will/.venvs/genresearch/bin/python bash scripts/validate_stage3.sh results/evidence/stage3-check
```

Para repetir escolha destino novo; índice da etapa 2 deve existir. Watchdogs
externos de 30 s nos serviços e 60 s nos testes. Prazo interno cooperativo não
cancela E/S já iniciada. Ganho de cache é estimativa bruta, não conclusão
experimental; single-flight de seguidores conta como miss separado de hit.
Etapa 4 concluída abaixo; matriz e análise seguem pendentes.

## Etapa 4 — concluída, verificada no WSL

Implementada experiments/demonstrate_race.py: duas threads observam miss com
barreira e duplicam trabalho apenas em processo isolado; correção reutiliza o
SharedCache da execução normal com coordenação por chave, cálculo fora do lock.
Watchdog de processo 5 s, coordenação 2 s, encerramento/kill com confirmação.
17 testes passaram, incluindo duplicação 2 → 1, resultados iguais, ordem dos
misses e teste de timeout com processo encerrado e contagem indisponível=null.

CLI executado no WSL Python 3.14.4 com timeout externo 15 s: run
7309c1af68234c8aa1f17d02d92f4737 em results/raw/stage4. Versão incorreta 2
cálculos/1 duplicado; corrigida 1 cálculo/0 duplicados. Ambos com resultados
iguais, exit code 0 e nenhum trabalhador/processo restante.
Evidências: results/evidence/stage4-validation/tests.txt e demo.json;
explicação, tabela e limites em docs/synchronization.md.

Comandos reais executados, na raiz do projeto Linux:

```bash
export PYTHONPATH=src:.
timeout 60 /home/will/.venvs/genresearch/bin/python -m unittest discover -s tests -v
timeout 15 /home/will/.venvs/genresearch/bin/python experiments/demonstrate_race.py
```

Podem ser repetidos: cada demonstração cria destino UUID novo. Sem pressão de
memória nem alteração de swap/cache do kernel. O modo incorreto não é importado
pela aplicação normal. Custo é espera simulada; tempos incluem instrumentação e
não comprovam ganho de desempenho. Matriz executada abaixo; análise e entregas pendentes.

## Matriz — executada e auditada

Plano/executor/worker limitado e análise tabular implementados. Lote final
results/raw/matrix/15c7fb31a435409597342b40f0d70665, 33/33 execuções válidas
(11 condições × 3), 720 consultas concluídas e 72 erros intencionais de índice
ausente. Sem perdas, duplicações, recusas inesperadas ou threads restantes.
Fatores: trabalhadores 1/2/4, corpus 12/48/192 documentos, cache 0/1/3.
read/mmap equivalentes nas três repetições. C5 moderado, sem forçar thrashing;
swap amostrado 0 B. C6 recuperação entre processos com índice disponível.

Limites reais auditados: RLIMIT_AS 512 MiB, RLIMIT_CPU 30 s, watchdog 45 s.
Aquecimento separado; plano, hashes, configurações, consultas e dados brutos
preservados. Primeiro lote e2ccf330512e4601a21861221ba382a1 preservado; não
misturar com o final, de coleta ampliada. 19 testes passaram. Auditoria final
conferiu IDs/logs/limites/recursos/contexto; resultados em matrix-final.
Auditoria inicial rejeitou E/S null; corrigida sem alterar dados. /proc/self/io
não existe neste ambiente, portanto contadores E/S/syscalls por processo null.
Tabelas derivadas em results/summary/matrix-15c7fb31, runs.csv/aggregates.json.

Comandos, protocolo e limites em docs/experiments.md. Pendente: gráficos e
interpretação completa, evidências complementares processos/syscalls/E/S,
relatório, slides, vídeo e reprodução em clone limpo Linux.

## Análise e gráficos — concluídos, revisão humana pendente

Cinco gráficos PNG/SVG gerados de dados reais: read/mmap (tempo/RSS/VSZ/faltas),
trabalhadores (vazão/p95/fila), cache (tempo/hits/p95), corpus/contexto e
sincronização. Dispersão mostra média ± desvio padrão amostral e três pontos.
Diagnósticos de etapas e tabela editorial em results/analysis/matrix-15c7fb31.
Explicação das questões do guia em docs/analysis.md: inclui lote não variado,
relações com RAG/checkpoints/GPU, contenção não isolada e limites WSL/sleep.

Matplotlib 3.10.8 instalado no venv após medições; dependências registradas em
requirements-analysis-lock.txt. Não altera versões utilizadas nos runs passados.
Cinco PNG inspecionados visualmente, sem cortes de textos/eixos. Auditoria
verify_analysis.py confirmou 364 hashes de entrada intactos, 33 diagnósticos e
agregação/arquivos de gráficos válidos (verification.txt). Sem novos experimentos.

Resultados interpretados com limites: mmap reduziu janela média neste recorte,
mas teve 24 major faults/run sem E/S física disponível; cache 1 não melhorou
p95; C5 não aumentou claramente RSS/p95 e não causou swap nas amostras; ganho
de trabalhadores não é promessa de paralelismo CPU. Fonte técnica consultada:
documentação Python threading 3.14 e Linux /proc, links em docs/analysis.md.

## Evidências complementares — concluídas no WSL

Implementados collect_evidence.py, evidence_worker.py e verify_evidence.py.
Duas cargas instrumentadas read/mmap concluíram 24 consultas cada, sem perdas,
duplicações ou threads de trabalho restantes. ps e /proc registraram seis threads
simultâneas, com dois produtores e dois consumidores confirmados na série.
strace registrou criação de threads, futex, leitura/escrita e mapeamento;
corpus/índice tiveram 0 mapeamentos/read e 48/mmap. GNU time, vmstat e iostat
coletados com encerramento automático. RLIMIT_AS 512 MiB, CPU 30 s e watchdog
30 s; nenhum cache do kernel/swap alterado.

Dados: results/evidence/linux-tracing-20261010; auditoria de 51 hashes íntegros
em results/summary/linux-tracing-20261010-verified. Primeira auditoria rejeitou
nome de thread ainda não aplicado no snapshot; corrigida para confirmar papéis
na série completa, preservando dados. Interpretação e comandos em docs/evidence.md.
Traces não agregados à matriz: geração 0,05 s e instrumentação alteram tempos.
/proc/PID/io continua ausente; E/S física por processo permanece indisponível.
Retornos EAGAIN/ETIMEDOUT em futex separados de falhas de consulta.

Relatório e slides adiados por solicitação da equipe, sem preparação nesta etapa.
Pendentes: revisão humana da interpretação, contribuições verdadeiras, vídeo,
reprodução em clone limpo Linux e entregas acadêmicas quando autorizadas.

## Organização para estudo da equipe

Criado docs/overview.md com fluxo da aplicação, mapa dos arquivos, etapas,
resultados reais, conceitos essenciais e ordem de estudo. README aponta para
o roteiro. Atualizadas referências antigas de pendência de evidências em
experiments/analysis; sem novos experimentos ou alterações nos dados brutos.
Relatório e slides continuam adiados.

## Preparação para GitHub

Revisados arquivos, tamanhos e padrões comuns de credenciais. Preparados código,
testes, configurações, documentação e resultados/evidências reais para staging.
.gitignore exclui ambientes, caches, dados gerados e planejamento de outra disciplina;
.gitattributes preserva bytes dos resultados para manter checksums no checkout.
Seleção explicada em docs/github.md. Sem alteração dos dados brutos, sem commit
ou push e sem afirmar reprodução em clone limpo Linux.
