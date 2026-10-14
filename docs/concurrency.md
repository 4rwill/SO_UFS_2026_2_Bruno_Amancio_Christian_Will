# Fila, cache e logs concorrentes

serve executa uma carga local finita, sem HTTP. Configuração em concurrent.json:
2 produtores, 2 consumidores, fila 4, cache 3, timeout de admissão 1 s,
prazo cooperativo 10 s, amostragem 0,01 s, 12 consultas. Limites configuráveis:
até 8 produtores/consumidores, fila/cache até 100, até 200 consultas, texto até
4096 bytes, tempos até 60 s. Os limites de corpus e índice continuam valendo.

Threads permitem sobrepor E/S e sleep de geração (espera simulada); não se
afirma ganho de CPU com threads Python. Todos compartilham índice em disco,
cache, fila, log e processo. RSS é do processo, não deve ser somado por thread.
O pipeline ainda abre/valida arquivos por miss, sem índice residente compartilhado.

Queue fornece condição e mutex para put/get. Carimbo de entrada é colocado em
_put, sob mutex, após obter espaço; _get registra retirada sob o mesmo mutex.
Espera na fila = retirada − admissão; espera de admissão = admissão − chegada.
Fila cheia resulta em recusa explícita, sem perda silenciosa. Após produtores
encerrados, Event sinaliza que não haverá novas entradas; consumidores drenam
e encerram ao get vazio. qsize não decide correção. Contadores/área temporal
da ocupação são atualizados sob mutex da Queue: média ponderada pelo tempo.

Prazo global é cooperativo: recusa entradas e falha tarefas ainda não iniciadas
após o prazo. Operações em execução terminam; não se pode cancelar com segurança
uma thread bloqueada em E/S do sistema. Comandos publicados usam timeout externo
30 s como watchdog do processo. Não há promessa de limite rígido interno para
E/S bloqueada. Se o watchdog matar o processo, artefatos podem ficar incompletos
e o manifesto running deve ser tratado como execução interrompida, nunca válida.
Tarefas de falha não impedem processamento das demais.

Cache LRU usa lock para busca, contadores, pending e eviction. Cálculo ocorre
fora do lock; Event por chave permite single-flight. Seguidores aguardam resultado
ou exceção com timeout; falha não é cacheada e tentativa posterior pode calcular.
Uma cópia protege valores cacheados contra alteração pelo chamador. Capacidade
0 desativa armazenamento/coordenação, cada busca é miss. Miss é consulta sem
valor pronto, inclusive seguidor; coalesced conta esses seguidores separadamente.
Hit rate = hits/(hits+misses), miss rate equivalente; sem buscas retorna null.

Chave inclui consulta casefold com espaços normalizados (preserva pontuação),
SHA-256 dos metadados com checksums corpus/índice, dimensões, top-k, limite de
contexto, atraso de geração e modo read/mmap. Corpus/índice devem permanecer
imutáveis durante um run; mudança de versão entre lookup/cálculo é rejeitada.
Cache com resultado pronto não relê corpus/índice, apenas os metadados.

EventLog serializa linhas JSONL e sequência sob lock, registrando chegada,
entrada/saída da fila, cache, etapas de loading/retrieval/generation, falhas,
resultado final e encerramento. O lock cobre somente escrita, não cálculo.
Horário civil UTC tem fuso; durações usam monotonic. Logging interfere nos tempos.

Cada run UUID salva manifest, requests, resources, events e summary. Registros
por consulta incluem ID, ordinal, produtor, trabalhador, tempos, resultado/erro
e status completed/failed/rejected. Configuração comum está no manifesto.
requests é ordenado por ordinal para leitura; events mostra ordem real concorrente.
resources amostra RSS/VSZ, MemAvailable, faltas cumulativas, ocupação e número de
threads; não garante capturar picos. Métricas ausentes ficam null.

Vazão = concluídas/janela do serviço (início antes do lançamento das threads até
join dos consumidores, incluindo encerramento). Utilização por trabalhador =
tempo ocupado/janela; ocupado inclui recuperação, geração e espera single-flight.
Latência = fim − chegada, incluindo admissão/fila; média/mediana/p95 só sobre
concluídas, p95 nearest-rank com n informado. Falhas/recusas têm contagens separadas.

result em um hit/coalesced conserva contexto e tempos da consulta originalmente
calculada; processing_s é o tempo efetivamente observado para a requisição atual.
cache_avoided_s_estimate soma o total original de etapas reutilizadas: estimativa
bruta, não economia líquida comprovada, especialmente para seguidores que esperam.
A comparação entre condições sem/com cache está em docs/analysis.md.

## Verificação real no WSL

15 testes passaram: corpus/pipeline, LRU e cópia, desativação, single-flight de
falha/retentativa, 2 produtores/2 consumidores, erro e recuperação após arquivo
ausente, saturação, prazo e encerramento. Scripts verificam IDs únicos, nenhum
item silenciosamente perdido, sequência/JSONL íntegros e ordem admissão/retirada/fim.

Evidências finais em results/evidence/stage3-check:

| Cenário CLI | Concluídas | Falhas | Recusadas |
|---|---:|---:|---:|
| Normal, 12 consultas | 12 | 0 | 0 |
| Consulta vazia controlada, 4 consultas | 3 | 1 | 0 |
| Fila 1, cache 0, admissão 0,001 s, 30 consultas | 3 | 0 | 27 |

Todos com perdas=0, duplicações=0, fila final vazia e nenhuma thread de trabalho
viva. Normal retorna código 0; runs com falhas/recusas retornam 2 e preservam
artefatos. Esses números descrevem os runs observados, não expectativa estável
para novas execuções: escalonamento e saturação variam. Não são a matriz C1–C6.
A demonstração isolada de duplicação e correção está em docs/synchronization.md.

A validação funcional usada como evidência é stage3-check; ensaios anteriores
foram preservados, sem mistura com o lote da matriz.
