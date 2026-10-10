# Evidências Linux — 10/10/2026

Coleta real no Ubuntu/WSL2, separada da matriz de desempenho. Foram executadas
duas cargas instrumentadas, read e mmap, com 24 consultas cada, cache desativado,
dois produtores, dois consumidores e espera simulada de geração de 0,05 s.
O worker inclui 0,2 s iniciais para permitir observação do PID. Essa configuração
e o custo do tracing impedem comparar seus tempos diretamente com a matriz.

## Arquivos e reprodução

Dados brutos: `results/evidence/linux-tracing-20261010`. Cada modo contém trace,
GNU time, ps, snapshots /proc, série de threads, vmstat, iostat, configuração,
saída e artefatos da aplicação. Versão instalada: strace 6.19; GNU time 1.9.
Auditoria derivada: `results/summary/linux-tracing-20261010-verified`, com
`facts.json`, `syscalls.csv` e `verification.txt`. Foram conferidos 51 hashes
SHA-256; dados brutos não foram alterados durante a análise.

Comandos executados na raiz do projeto no Ubuntu:

```bash
PYTHONPATH=src:. timeout 90 /home/will/.venvs/genresearch/bin/python scripts/collect_evidence.py --output results/evidence/linux-tracing-20261010
/home/will/.venvs/genresearch/bin/python scripts/verify_evidence.py results/evidence/linux-tracing-20261010 results/summary/linux-tracing-20261010-verified
```

Para repetir, escolher destinos novos: os scripts recusam sobrescrita.
Pré-requisitos: índice da etapa 2, strace, time, procps e sysstat disponíveis.
O coletor registra a linha completa de execução no manifesto. Usa strace -f
-yy -C com seleção de openat/read/write/mmap/munmap/futex/clone/clone3/
clock_nanosleep; read/write em formato raw evitam despejar o conteúdo dos buffers.
vmstat e iostat usam cinco amostras de um segundo, omitindo o relatório desde
o boot (-y). A observação de threads ocorre aproximadamente a cada 30 ms.
Limites: espaço virtual 512 MiB, CPU 30 s, watchdog 30 s e trace até 8 MiB;
o coletor encerra o grupo de processos se um limite de acompanhamento for atingido.

## Correção, processos e memória

| Modo | PID da aplicação | Máximo de threads observado | Concluídas | Perdas/duplicações | Threads de trabalho restantes |
|---|---:|---:|---:|---:|---:|
| read | 3475 | 6 | 24 | 0/0 | 0 |
| mmap | 3492 | 6 | 24 | 0/0 | 0 |

Papéis confirmados na série: thread principal, amostrador de recursos,
consumer-0, consumer-1, producer-0 e producer-1. O nome Linux do amostrador
aparece truncado como resource-sample. Uma thread pode aparecer inicialmente
como python antes de seu nome ser aplicado; por isso a auditoria usa toda a
série para confirmar papéis, além do snapshot simultâneo de seis threads.
A primeira auditoria rejeitou essa diferença de nome; a verificação foi corrigida
sem refazer a medição nem editar dados brutos.

ps -L evidencia LWPs do mesmo PID e /proc/PID/task confirma compartilhamento do
processo. Não somar o RSS repetido nas linhas de threads: compartilham o espaço
de memória. proc-maps registra regiões; proc-limits confirma 536870912 bytes
de limite de espaço virtual. Estado t durante strace indica parada por tracing,
sem evidência isolada de deadlock. Ambas as execuções terminaram com código 0.

GNU time registrou máximos de RSS de 38928 KiB/read e 39248 KiB/mmap, major
faults 7/50 e minor faults 200749/102541. Seu escopo inclui o processo strace e
descendentes, inicialização e janela de observação; não equivale à janela e
contadores amostrados da aplicação na matriz. São evidências instrumentadas,
sem conclusão de superioridade de um modo.

## Chamadas de sistema

| Chamada | read: chamadas | mmap: chamadas | Interpretação |
|---|---:|---:|---|
| read | 720 | 616 | Leituras de arquivos, runtime e outros descritores |
| openat | 511 | 505 | Abertura de arquivos, incluindo tentativas do runtime |
| mmap | 273 | 273 | Todos os mapeamentos, inclusive alocações e bibliotecas |
| futex | 6888 | 6818 | Espera e sinalização relacionadas à sincronização |
| clone3 | 5 | 5 | Criação das cinco threads adicionais |
| clock_nanosleep | 25 | 25 | Esperas simuladas e janela inicial de observação |
| write | 300 | 300 | Escritas observadas, incluindo artefatos e logs |

O filtro específico de corpus.bin/index.json encontrou **0 mapeamentos/read e
48/mmap**: dois arquivos por consulta. Os mapeamentos dos arquivos alvo usam
PROT_READ/MAP_SHARED. A contagem global igual de mmap não significa comportamento
igual sobre esses arquivos. A aplicação acessa e copia os bytes mapeados;
número de syscalls não mede quantidade de bytes nem E/S física.

O resumo do trace registra 1496/1440 retornos de erro em futex. EAGAIN pode
indicar que o valor mudou antes de esperar e ETIMEDOUT que a espera venceu;
esses retornos não são contagem de falhas de consulta. A aplicação concluiu
as 48 consultas. Também não interpretar tentativas openat com ENOENT como
falhas da aplicação. Contagens abrangem o processo e descendentes e somente
as chamadas selecionadas. Percentuais/tempos de strace têm custo de
instrumentação e não identificam, por si, o gargalo da matriz.

## E/S e limites WSL

/proc/PID/io não existe neste ambiente; a tentativa e o erro foram registrados.
Contadores indisponíveis da aplicação continuam null, inclusive nos runs
anteriores. vmstat/iostat descrevem a instância Linux e dispositivos observados,
não atribuem atividade exclusivamente ao projeto nem identificam a E/S física
do SSD Windows. iostat registrou atividade de leitura em sdd; isso não prova
que os bytes do corpus em /mnt/c originaram essa leitura. GNU time reportou
0 para swaps e filesystem inputs/outputs; esses zeros observados não autorizam
concluir ausência de toda E/S física no host.

Não houve limpeza de caches do kernel, alteração de swap ou tentativa de OOM.
Tracing complementa evidências de processos, threads, memória, armazenamento
e sincronização; as restrições do WSL permanecem explícitas. A equipe deve
revisar a interpretação e conservar os artefatos usados na entrega.

Fontes técnicas consultadas: [strace](https://strace.io/),
[Linux FUTEX_WAIT](https://www.man7.org/linux/man-pages/man2/FUTEX_WAIT.2const.html)
e [documentação /proc do kernel](https://www.kernel.org/doc/html/latest/filesystems/proc.html).
Coleta, auditoria e texto preparados com assistência Codex; não foram inferidas
contribuições individuais da equipe. Relatório e slides adiados a pedido da equipe.
