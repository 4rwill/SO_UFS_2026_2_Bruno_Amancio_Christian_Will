# Matriz experimental executada — 10/10/2026

Lote final Linux/WSL 2 Python 3.14.4:
results/raw/matrix/15c7fb31a435409597342b40f0d70665. Plano em matrix.json;
executor run_matrix.py; worker limited_worker.py. 11 condições × 3 repetições,
33/33 válidas: 720 consultas concluídas, 72 erros intencionais de índice ausente.
Sem perdas, duplicações, recusas inesperadas ou threads restantes.
Primeiro lote e2ccf330512e4601a21861221ba382a1 preservado como coleta inicial;
não misturar com o final, que possui CPU/swap/cache/E/S na amostragem.

## Protocolo e controles

Processo novo por repetição, execuções sequenciais. Mesmas 24 consultas/ordem,
semente 202602, 9 textos distintos; 18/24 pertencem a três textos recorrentes,
6 têm sufixo distinto. Repetições após primeira ocorrência: 15/24.
Fila 4, 2 produtores, geração sleep 0,01 s (espera, não CPU/IA), default 2
consumidores, read, cache 0, top-k 3/contexto 512 bytes. Logging igual.
Duas consultas sequenciais de aquecimento, separadas em warmup.json antes do
serviço; serve cria cache novo vazio. C6 ausente sem aquecimento. Cache de páginas
pode estar aquecido; não chamar primeira execução de disco frio nem limpar cache.

| Série | Comparação |
|---|---|
| C1/C2 | read/mmap; mesmos dados e acesso integral; restante idêntico |
| C3 | trabalhadores 1/2/4, com 2 produtores; 2 reutiliza C1 |
| Corpus | pequeno/médio/maior; pequeno reutiliza C1 |
| C4 | cache 0/1/3; 0 reutiliza C1 |
| C5 | corpus maior, top-k 32/contexto 8192 versus 3/512 de corpus-large |
| C6 | caminho de índice ausente, depois processos novos com índice disponível |

C5 combina top-k/contexto: não isola efeito exclusivo de cada um. É aumento
moderado de carga, sem aproximar RAM do limite; não representa pressão intensa.
C6 não apaga arquivos reais; recuperação é entre processos/configurações. A
recuperação de arquivo restaurado no serviço foi testada na etapa 3.

| Corpus | Documentos | Texto bytes | Índice bytes | Fragmentos |
|---|---:|---:|---:|---:|
| Pequeno | 12 | 20797 | 75314 | 96 |
| Médio | 48 | 83270 | 302273 | 384 |
| Maior | 192 | 333022 | 1206322 | 1536 |

Mesma semente, 24 frases/documento, fragmentos 256/sobreposição 32/vetores 64.
Manifestos fonte/checksums/metadados/configs salvos no lote. Corpus gerados no
data/generated podem ser recriados pelo runner; dados brutos não são editados.

## Limites e fontes

Pré-checagem exige MemAvailable >=1 GiB e disco >=256 MiB. Observado cerca de
3,2 GiB disponíveis e 322 GiB de disco. RLIMIT_AS 512 MiB (espaço virtual, não
RSS), RLIMIT_CPU 30 s; /proc/self/limits salvo e auditado. Watchdog 45 s por
processo, orçamento 900 s por lote, externo 950 s; prazo cooperativo serviço 30 s.
Sem OOM global, alterações de swap ou limpeza de cache. Projeto /mnt/c 9p/DrvFS;
RAM/CPU do guest não descrevem todo Windows; GPU não utilizada.

RSS/VSZ, MemAvailable, Cached, swap usado, CPU e faltas minor/major amostrados;
máximo amostrado não é pico garantido. Contadores cumulativos são analisados por
delta entre primeira/última amostra, após aquecimento. Swap foi 0 em todas as
amostras do lote final, sem extrapolar ausência de thrashing para cargas maiores.
Cached é campo Linux Cached, não soma de todos os caches.

/proc/self/io não existe no ambiente: contadores E/S e syscalls por processo
ficam null, não zero (proc-io-check.txt). Bytes lógicos de arquivos são exportados
pelo pipeline; iostat coletado antes da carga é global, não substituto de E/S por
requisição. Coleta complementar de syscalls concluída: veja docs/evidence.md;
E/S física por processo continua indisponível.

## Auditoria e tabelas

19 testes passaram, incluindo agregação conhecida e valores ausentes. Auditoria
de 33 runs conferiu JSONL, sequências, IDs, fila, contexto, limites e aquecimento.
C1/C2 tiveram conteúdo/trechos/resposta/versão/bytes iguais nas três repetições.
Evidências em results/evidence/matrix-final. Primeira auditoria exigiu E/S
disponível e falhou; corrigida para aceitar null sem editar os dados brutos.

Runs incluem manifest/requests/resources/events/summary, warmup e limites.
Manifesto do lote registra plano, data, consultas e hashes de código; cada
worker registra commit/estado/config. Falhas inesperadas seriam registradas em
executions.jsonl sem repetição inventada. Tabelas runs.csv e aggregates.json em
results/summary/matrix-15c7fb31: média, desvio padrão amostral, min/max/n por
condição. p95 é por consultas em cada run (24 nas condições bem-sucedidas),
nearest-rank; não percentil de três repetições. Falhas controladas têm condição
separada; nenhuma indisponibilidade foi convertida em zero.

Comandos realmente executados, na raiz do projeto Linux:

```bash
export PYTHONPATH=src:.
timeout 950 /home/will/.venvs/genresearch/bin/python experiments/run_matrix.py --config experiments/configs/matrix.json --repetitions 3
/home/will/.venvs/genresearch/bin/python scripts/verify_matrix.py results/raw/matrix/15c7fb31a435409597342b40f0d70665
/home/will/.venvs/genresearch/bin/python experiments/analyze.py --input results/raw/matrix/15c7fb31a435409597342b40f0d70665 --output results/summary/matrix-15c7fb31
```

Runner cria lote UUID novo; análise exige saída nova. Gráficos, interpretação
e evidências complementares concluídos; entregas e revisão humana pendentes.
