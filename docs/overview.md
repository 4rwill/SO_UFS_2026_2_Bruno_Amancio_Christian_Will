# Como entender e organizar o projeto

Este é um roteiro de estudo e navegação para a equipe. Não é o relatório final
nem uma apresentação. Os registros detalhados e comandos estão no README e
nos documentos vinculados abaixo.

## O que foi construído

Uma aplicação local de linha de comando inspirada em RAG: ela busca trechos de
documentos para montar o contexto de uma resposta. O objetivo acadêmico é estudar
memória, arquivos, filas, cache, threads e sincronização.

O corpus é sintético e reproduzível por semente. Os vetores são representações
lexicais determinísticas por hashing SHA-256, não embeddings de um modelo.
A resposta é simulada e usa sleep para representar espera. Não houve inferência
de IA, treinamento ou uso de GPU.

Fluxo completo:

```text
Gerar documentos → fragmentar → vetorizar → salvar corpus/índice/metadados

Produtores → fila limitada → consumidores → procurar no cache
                                            ├─ hit: reutilizar resultado
                                            └─ miss: recuperar top-k
                                                     → limitar contexto
                                                     → simular resposta
                                                     → publicar no cache
                         → registrar resultado, eventos e métricas
```

## Etapas realizadas

1. **Ambiente e fundação:** configurado Ubuntu/WSL2 e venv; coletados CPU, RAM,
   swap, kernel, discos e versões. Criado gerador determinístico de documentos.
2. **Pipeline sequencial:** fragmentação de 256 caracteres com sobreposição 32,
   vetores de 64 dimensões, persistência com checksums, busca top-k 3, contexto
   de até 512 bytes e resposta simulada. read/mmap acessam os mesmos dados e
   produzem resultados equivalentes; mmap copia os bytes neste projeto.
3. **Concorrência:** produtores alimentam fila limitada; consumidores processam
   consultas. Cache LRU compartilhado, coordenação por chave, logs protegidos,
   timeouts, falhas explícitas e encerramento sem perdas silenciosas.
4. **Sincronização:** demonstração isolada força dois trabalhadores a calcular
   a mesma consulta. Sem coordenação: dois cálculos. Com single-flight: um
   calcula e o outro aguarda. A aplicação normal sempre usa proteção.
5. **Experimentos:** 11 condições com três repetições cada, processos novos,
   consultas fixas, aquecimento separado e limites de recursos.
6. **Análise:** tabelas e cinco gráficos gerados automaticamente dos dados reais,
   com dispersão entre repetições e limitações documentadas.
7. **Evidências:** observação Linux de processos/threads, memória e syscalls,
   separada da matriz porque tracing altera desempenho.

## Onde encontrar cada parte

| Local | Função | Quando consultar |
|---|---|---|
| `AGENTS.md` | Requisitos e critérios do trabalho | Conferir escopo acadêmico |
| `README.md` | Instalação e comandos executados | Rodar o projeto |
| `src/genresearch/` | Aplicação, cache, fila, recuperação e métricas | Estudar implementação |
| `tests/` | Testes de determinismo, equivalência, concorrência e falhas | Entender garantias de correção |
| `experiments/configs/` | Parâmetros e plano experimental | Entender o que variou |
| `experiments/` | Matriz, demonstração e análise | Reproduzir experimentos |
| `scripts/` | Coleta e auditoria | Conferir evidências |
| `data/` | Documentação e corpus gerado | Entender entrada sintética |
| `results/raw/` | Execuções brutas | Investigar origem de um número |
| `results/summary/` | Tabelas e auditorias derivadas | Conferir agregação |
| `results/analysis/` | Gráficos e proveniência | Interpretar comparações |
| `results/evidence/` | Ambiente, testes, traces e observações Linux | Demonstrar execução e comportamento |
| `docs/` | Explicações e status | Estudar o projeto |

Dados brutos devem permanecer intactos. Não misturar lotes iniciais com o lote
final. Não apagar ensaios anteriores para melhorar artificialmente a aparência
dos resultados. Geradores e análises normalmente exigem destinos novos.

## Resultados que podemos afirmar

Lote principal: `results/raw/matrix/15c7fb31a435409597342b40f0d70665`.
Foram 33 execuções válidas, 720 consultas concluídas e 72 falhas intencionais
de índice ausente. Não houve perdas, duplicações ou threads restantes.
Os 19 testes da última validação da matriz passaram; isso não significa que
sejam 19 experimentos de desempenho.

| Comparação | Observação no recorte executado |
|---|---|
| read / mmap | Vazão média 52,90 / 60,72 consultas/s; resultados equivalentes |
| 1 / 2 / 4 consumidores | Vazão média 26,93 / 52,90 / 74,03 consultas/s |
| Cache 0 / 1 / 3 entradas | Hit rate médio 0 / 6,94 / 31,94% |
| Corpus pequeno / médio / maior | RSS máximo amostrado médio 34,29 / 42,48 / 53,83 MiB |
| Corrida / correção | Dois cálculos / um cálculo para a mesma chave |

Cache de capacidade 1 não melhorou o p95, apesar da pequena redução da janela
total. Corpus maior aumentou memória e latência; contexto maior não produziu
aumento claro de RSS no teste moderado. Swap foi zero nas amostras; não foi
demonstrado thrashing. As conclusões detalhadas estão em [analysis.md](analysis.md).

Coleta complementar: 48 consultas concluídas, seis threads simultâneas por
processo, 51 arquivos brutos auditados. Mapeamentos específicos de corpus/índice:
zero no modo read e 48 no modo mmap. Não confundir esses números com todas as
chamadas mmap do runtime. Veja [evidence.md](evidence.md).

## Conceitos que cada integrante deve conseguir explicar

- **Fila:** absorve requisições até sua capacidade; excesso gera espera ou recusa.
- **Cache LRU:** reutiliza resultados e remove a entrada menos recentemente usada.
  Miss é ausência de resultado pronto, não erro de execução.
- **Single-flight:** coordena trabalho em andamento para a mesma chave; um calcula,
  seguidores aguardam. Proteger só a escrita do dicionário não evita duplicação.
- **Threads:** compartilham memória e recursos; precisam de sincronização.
  Os ganhos medidos são desta carga com espera/E/S, não prova de ganho CPU.
- **read/mmap:** são formas de acessar arquivos; este mmap ainda copia e faz parse
  integral. Cache da aplicação e cache de páginas do SO são distintos.
- **RSS/VSZ:** RAM residente e espaço virtual; não representam a mesma coisa.
- **p95/vazão:** cauda de latência das consultas e consultas concluídas por segundo.
  Média de três repetições não substitui o percentil calculado por requisições.
- **Faltas de página:** minor/major foram observadas, mas não quantificam sozinhas
  bytes físicos ou swap. A causa das faltas major do mmap não foi isolada.

## Ordem sugerida de estudo

1. Ler este roteiro e [environment.md](environment.md).
2. Ler [architecture.md](architecture.md) e acompanhar uma consulta no código.
3. Ler [concurrency.md](concurrency.md) e [synchronization.md](synchronization.md).
4. Ler [experiments.md](experiments.md), depois [analysis.md](analysis.md).
5. Conferir [evidence.md](evidence.md) e [status.md](status.md).
6. Executar os comandos de validação do README em destinos novos e comparar
   resultados funcionais; tempos podem variar entre computadores e execuções.

## O que ainda depende da equipe

Revisar e compreender as interpretações; confirmar equipe de 5–7 integrantes,
contribuições verdadeiras, nome público do repositório, canal e fuso da entrega.
Verificar reprodução a partir de clone limpo Linux. Preparar posteriormente
relatório de 8–12 páginas, slides, vídeo com todos e links exigidos.

Relatório e slides permanecem adiados. Este roteiro não inventa participação
humana, resultados nem conclusões para métricas indisponíveis. No WSL,
/proc/PID/io continua indisponível e tracing não substitui E/S física por processo.
