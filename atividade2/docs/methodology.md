# Memória e definições de medição

O ambiente e as ferramentas estão em [environment.md](environment.md); condições, comandos e controles da matriz em [experiments.md](experiments.md).

## Memória virtual e arquivos

- `MemFree`: memória atualmente livre.
- `MemAvailable`: estimativa de memória disponibilizável para novas cargas sem swap, incluindo páginas recuperáveis.
- `Cached`: campo de cache de páginas do Linux, sem equivaler à soma de todos os caches.
- Swap usada: páginas armazenadas fora da RAM, distinta da capacidade configurada.
- RSS: páginas residentes do processo. VSZ: espaço de endereçamento virtual, incluindo reservas e mapeamentos; não equivale a RAM consumida.
- Faltas minor/major: contadores observados por delta entre primeira e última amostra; não são diretamente bytes físicos de disco.

O cache de páginas pode evitar releituras físicas e pode ser recuperado: não é necessariamente memória desperdiçada. Datasets, índices, embeddings e checkpoints dependem da residência das páginas e do padrão de acesso. Esta implementação carrega integralmente arquivos pequenos, inclusive no modo mmap.

## Tempo, fila, cache e correção

Duracões usam relógio monotônico; manifestos e eventos registram horário civil com fuso. Vazão é conclusões/janela do serviço; latência inclui admissão e fila. Espera na fila é retirada menos admissão; espera de admissão é registrada separadamente. Ocupação média é ponderada pelo tempo. Utilização de trabalhador inclui espera, sem equivaler a CPU.

Média/mediana/p95 consideram consultas concluídas, com p95 nearest-rank e tamanho da amostra informado. As tabelas agregam média ± desvio padrão amostral entre três repetições, sem testes de significância. Média das medianas por execução não é mediana conjunta.

Hit rate = hits/(hits+misses); miss rate = 1 − hit rate. Seguidores single-flight são misses/coalesced, não hits. Misses de cache não são erros de execução. `cache_avoided_s_estimate` é estimativa bruta, sem desconto de espera/logging; as comparações entre configurações sustentam a análise da duração observada.

Manifestos, requisições, recursos, eventos e resumos preservam parâmetros, IDs, resultados e falhas. Verificações conferem integridade JSONL, sequência, perdas, duplicações e encerramento. Dados brutos permanecem imutáveis; indisponibilidade é `null`, nunca um zero atribuído artificialmente.

## Limites da observação

Máximos amostrados de RSS/VSZ podem perder picos. `/proc/PID/io` não existia neste ambiente: E/S por processo ficou indisponível. `vmstat`/`iostat` descrevem a instância Linux/dispositivos, sem atribuição exclusiva ao projeto ou ao SSD Windows. Tracing tem sobrecarga e foi realizado separadamente da matriz. Não houve limpeza de caches, alteração de swap ou tentativa de OOM global. C5 foi moderado, sem comprovar pressão intensa ou thrashing.

Fonte técnica: [documentação /proc do kernel Linux](https://www.kernel.org/doc/html/latest/filesystems/proc.html).
