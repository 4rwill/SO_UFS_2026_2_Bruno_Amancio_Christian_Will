# Guia do projeto: GenResearch-Servidor — Sistemas Operacionais AV2

## 1. Finalidade e origem

Este arquivo orienta o Codex e a equipe na implementação, execução, análise e documentação da Atividade 2 de Sistemas Operacionais, 2026/2. Coloque-o na raiz do repositório como `AGENTS.md`.

Fonte dos requisitos acadêmicos: `Atividade_2_Sistemas_Operacionais_2026_2_submetida.pdf`, fornecido pela equipe. As exigências abaixo foram transcritas e organizadas a partir desse documento. As escolhas técnicas identificadas como sugestões são decisões deste guia, não imposições do docente. Se houver atualização do enunciado, registrar e resolver a divergência antes de alterar o escopo.

Objetivo: investigar como memória principal, memória virtual, armazenamento, caches, filas e sincronização afetam desempenho, estabilidade e correção de uma aplicação simplificada inspirada em IA generativa/RAG.

O sucesso depende de código reproduzível e evidências experimentais, não da qualidade textual das respostas.

## 2. Prazos e responsabilidades humanas

- Equipe obrigatória: 5 a 7 discentes.
- Entrega: 20/10/2026, às 23h59, conforme enunciado. Confirmar o fuso e canal de submissão com o docente.
- Apresentação oral: 21/10/2026; 10 a 12 minutos e 3 a 5 minutos de perguntas.
- Vídeo: até 20 minutos, com participação de todos.
- Relatório: PDF de 8 a 12 páginas, excluídos anexos.
- Todos devem participar da apresentação oral e do vídeo e compreender o código e os resultados.
- A equipe deve confirmar a regra de nome do repositório público, não especificada no PDF.
- Registrar contribuições reais de cada integrante; não inventar nomes, participações ou referências.
- O Codex pode preparar código, testes, experimentos, análise e rascunhos. A equipe deve executar ou supervisionar as medições, validar a interpretação, gravar o vídeo e realizar a apresentação.

## 3. Instruções de trabalho para o Codex

1. Inspecionar o repositório antes de editar. Reutilizar o que já existe e preservar alterações da equipe.
2. Ler este guia, o enunciado disponível e `docs/status.md`, se existir.
3. Implementar por etapas verificáveis, com código simples e comentários úteis ao aprendizado.
4. Não inventar medições, logs, screenshots, comandos executados, conclusões ou sucesso de testes. Dados de exemplo devem ser explicitamente identificados e separados dos resultados reais.
5. Não substituir falhas de medição por zero. Registrar `null`/indisponível e explicar a limitação.
6. Nunca afirmar que um experimento foi executado quando apenas foi implementado.
7. Se Linux não estiver acessível, preparar o projeto e os comandos de execução; registrar que os experimentos permanecem pendentes. Não usar medições Windows como se fossem Linux.
8. Não publicar chaves, tokens, senhas, arquivos `.env`, dados pessoais, documentos sigilosos ou pesos de modelos. Usar dados públicos, sintéticos ou anonimizados.
9. Não instalar serviços pagos nem tornar APIs externas obrigatórias. A versão mínima deve funcionar localmente.
10. Não causar falta de memória no computador inteiro, alterar swap global ou limpar caches do kernel automaticamente. Experimentos intensivos devem ter limites e timeout.
11. A versão deliberadamente incorreta deve existir apenas na demonstração isolada de sincronização. A execução normal deve usar proteção correta.
12. Manter `docs/status.md` com implementado, verificado, executado, pendente, bloqueios e comandos de continuidade. Marcar checkboxes somente com evidência.
13. Documentar decisões, fontes de terceiros e uso de assistência por IA conforme as regras da instituição.
14. Ao concluir uma etapa, informar o que mudou, como foi verificado e o que ainda depende da equipe.

## 4. Pré-requisitos

### Necessários

- Repositório Git público no GitHub, criado pela equipe com nome conforme o docente.
- Linux nativo, WSL, máquina virtual ou contêiner, devidamente documentado.
- Python 3 disponível no Linux e ambiente virtual isolado. Registrar a versão exata usada.
- Espaço em disco e memória suficientes para o corpus configurado; verificar antes de gerar arquivos maiores.
- Git, ferramentas básicas de observação Linux e uma forma de produzir PDF e slides.
- Local acessível para hospedar o vídeo e disponibilizar sua URL.

### Dependências sugeridas

- Biblioteca padrão: `queue`, `threading`, `mmap`, `sqlite3`, `logging`, `resource`, `hashlib`, `argparse`.
- `numpy`: vetores e busca por similaridade, se útil.
- `psutil`: amostragem de processos e memória, validando métricas disponíveis no Linux.
- `pandas` e `matplotlib`: agregação de resultados e gráficos.
- `pytest`: testes de correção, concorrência e reprodução.
- Ferramentas Linux: `time`, `procps`, `sysstat` e `strace`, quando disponíveis.

Fixar versões efetivamente testadas. Não é necessário Ollama, GPU, modelo real, chave de API, frontend web ou deploy para a versão mínima.

## 5. Escopo técnico sugerido

- Programa local com interface de linha de comando e serviço de processamento com trabalhadores; rede/HTTP é opcional.
- Documentos de texto sintéticos gerados com semente fixa, temas e consultas conhecidos.
- Fragmentação determinística, com tamanho e sobreposição configuráveis.
- Embeddings reais ou vetores simulados são permitidos. Usar representação determinística por hashing de termos como opção simples; não usar `hash()` nativo como identificador estável entre processos.
- Recuperação top-k por similaridade e contexto limitado por bytes ou tokens aproximados.
- Resposta simulada com custo configurável e resultado determinístico resumido.
- Corpus e vetores persistidos em arquivos; formato que permita leitura normal e `mmap` sobre os mesmos bytes.
- Metadados em JSON ou SQLite. Se usar SQLite, definir propriedade das conexões e serialização da escrita.
- Fila limitada de requisições e cache LRU compartilhado, com capacidade configurável.
- Logs estruturados em JSONL, com escrita concorrente protegida.

Justificar threads, processos ou tarefas assíncronas segundo a carga. Threads são um ponto inicial adequado para espera/E/S; não prometer ganho de CPU com threads Python. Se a geração usar `sleep`, identificá-la como simulação de espera e não como trabalho computacional. Se usar trabalho CPU, definir e documentar o cálculo realizado e seus limites.

## 6. Arquitetura e comportamento

```text
Documentos -> fragmentação -> vetores -> corpus/índice/metadados persistidos

Produtores -> fila limitada -> consumidores
                               -> cache compartilhado
                               -> recuperação quando houver cache miss
                               -> montagem de contexto
                               -> resposta/simulação
                               -> atualização do cache
                               -> resultado, métricas e logs
```

Cada requisição deve ter ID único, consulta, horário de entrada e parâmetros. Registrar entrada/saída da fila, início/fim das etapas e estado final. Encerrar com protocolo claro, sem consumidores presos ou requisições silenciosamente perdidas. Evitar usar `qsize()` para decidir correção; tratá-lo como observação aproximada ou manter contadores protegidos.

O cache deve registrar hits, misses, substituições e duração das etapas evitadas. Usar chave que inclua consulta normalizada, versão do corpus/índice e parâmetros relevantes. Consultas semanticamente distintas não devem ser confundidas. A taxa de erro do cache é a proporção de misses; separar de erros de execução.

## 7. Estrutura sugerida do repositório

```text
AGENTS.md
README.md
VIDEO.md
pyproject.toml ou requirements.txt
.gitignore
src/genresearch/
  cli.py, ingestion.py, storage.py, retrieval.py
  server.py, cache.py, metrics.py, logging_setup.py
experiments/
  configs/              # configurações e matriz experimental
  run_matrix.py         # execução e repetições
  demonstrate_race.py   # falha e correção isoladas
  analyze.py            # tabelas e gráficos
scripts/
  collect_environment.sh
  reproduce.sh
tests/
data/
  README.md             # origem/geração; evitar grandes arquivos no Git
results/
  raw/                  # dados reais por execução
  summary/              # tabelas derivadas
  figures/
  evidence/             # processos, threads, syscalls etc.
docs/
  status.md
  architecture.md
  methodology.md
  report.md
  contributions.md
  presentation.md
deliverables/
  report.pdf
  presentation.pdf ou presentation.pptx
```

Os nomes e módulos são sugestões. Preservar organização coerente se o projeto já tiver outra estrutura.

## 8. Plano de implementação e critérios de conclusão

### Etapa 1 — Ambiente e fundação (Parte A)

- [ ] Registrar distribuição/versão, kernel, CPU/CPUs, RAM/swap, disco/sistema de arquivos, GPU/VRAM se houver e modo de execução.
- [ ] Registrar linguagem, bibliotecas, modelo/ferramenta, commit, data e horário com fuso.
- [ ] Coletar `uname -a`, `cat /etc/os-release`, `lscpu`, `free -h`, `cat /proc/meminfo`, `lsblk`, `df -h`, `swapon --show`.
- [ ] Preparar coleta de `vmstat 1` e `iostat -xz 1` com encerramento automático.
- [ ] Explicar MemFree, MemAvailable, cache, swap e cache de páginas.
- [ ] Criar dependências, README inicial e gerador de corpus reproduzível.

Conclusão: ambiente documentado e corpus recriável por um comando.

### Etapa 2 — Pipeline sequencial (Parte B)

- [ ] Ler, fragmentar e vetorizar documentos.
- [ ] Persistir corpus, índice e metadados; registrar tamanhos e checksums.
- [ ] Recuperar top-k e limitar contexto; registrar trechos, bytes/tokens aproximados.
- [ ] Produzir resposta real local ou simulação documentada.
- [ ] Registrar tempos de ingestão, recuperação, resposta e total.
- [ ] Verificar leitura convencional e `mmap` com os mesmos resultados e mesmos dados.

Conclusão: uma consulta funciona de ponta a ponta e as métricas são exportadas.

### Etapa 3 — Concorrência, cache e logs (Partes B e D)

- [ ] Implementar fila limitada com pelo menos dois produtores e dois consumidores no cenário C3.
- [ ] Tornar número de trabalhadores, fila e cache configuráveis.
- [ ] Implementar cache compartilhado protegido e logs íntegros sob concorrência.
- [ ] Tratar fila cheia/vazia, timeout, falhas e encerramento.
- [ ] Verificar IDs processados, perdas, duplicações e integridade dos logs.

Conclusão: carga concorrente termina corretamente, inclusive diante de erro controlado.

### Etapa 4 — Demonstração obrigatória de sincronização (Parte D)

Escolha sugerida: duplicação de trabalho/cache em consultas simultâneas.

1. Dois trabalhadores consultam a mesma chave ausente.
2. Na versão sem proteção, uma barreira força ambos a observar o miss antes do cálculo, tornando a demonstração reproduzível.
3. Registrar duas execuções do trabalho para a mesma chave.
4. Corrigir com coordenação por chave em andamento (single-flight) ou mecanismo equivalente.
5. Comparar resultados, quantidade de cálculos, espera e contenção.

Não basta proteger apenas a atribuição ao dicionário. A coordenação deve abranger a decisão de calcular e permitir que os demais aguardem o resultado. Não manter lock global durante trabalho demorado sem discutir o custo. Não colocar uma barreira dentro de um lock de modo que a versão corrigida fique presa.

- [ ] Evidenciar compartilhamento e falha controlada.
- [ ] Evidenciar correção e trade-offs.
- [ ] Isolar demonstração com timeout e encerramento.

Deadlock não é obrigatório. Se escolhido, usar processo isolado, timeout, encerramento e explicar recuperação.

## 9. Matriz experimental (Partes C e E)

C1–C4 são obrigatórios. C5 e C6 devem ser executados quando possível; se não forem viáveis, justificar tecnicamente e apresentar alternativa equivalente. A falha controlada da Parte D é obrigatória independentemente de C6.

| ID | Comparação | Controles e evidências |
|---|---|---|
| C1 | Leitura convencional | Linha de base com `open/read`; tempo de abertura/leitura, memória e E/S |
| C2 | Leitura por `mmap` | Mesmo corpus, conteúdo acessado e padrão de leitura; validar equivalência com C1 |
| C3 | Concorrência e fila | Pelo menos 2 produtores e 2 consumidores; medir espera, utilização e vazão |
| C4 | Cache compartilhado | Cache desativado/ativado; consultas repetidas e distintas; hits/misses/substituições |
| C5 | Pressão de memória | Aumentar corpus, contexto ou lote dentro de limites; observar degradação e memória |
| C6 | Falha controlada | Arquivo ausente, índice indisponível ou saturação; evidenciar erro e recuperação |

### Três fatores mínimos sugeridos

1. Trabalhadores: 1, 2 e 4. A condição de 1 trabalhador serve de comparação; a configuração C3 com 2 produtores e 2 consumidores continua obrigatória.
2. Corpus: pequeno, médio e maior, com tamanhos em bytes definidos após verificar o equipamento.
3. Capacidade do cache: desativado, pequena e maior; valores explícitos no manifesto.

Leitura convencional versus `mmap` acrescenta outra comparação. Não é obrigatório cruzar todas as combinações: criar séries que alterem um fator por vez e justificar a matriz. Cada configuração deve ter pelo menos três repetições válidas.

### Protocolo

- Definir previamente consultas, quantidade, ordem/semente, proporção de repetidas, top-k, contexto, lote, fila, cache, modo de leitura e custo de geração.
- Usar o mesmo corpus e aplicativo, exceto na variável explicitamente alterada.
- Criar um processo novo para cada repetição quando possível; distinguir cache da aplicação de cache do sistema operacional.
- Separar aquecimento de medição e registrar ambos.
- Comparar primeira e segunda execução sem afirmar que a primeira tem disco/cache frio. Não limpar cache do kernel automaticamente; documentar o estado observado.
- Em `mmap`, acessar os dados equivalentes aos lidos no modo convencional. Medir somente o mapeamento não equivale a ler o arquivo.
- Registrar abertura/mapeamento separadamente do acesso completo; RSS e VSZ têm significados distintos.
- Registrar falhas de execução e não descartá-las silenciosamente. Não substituir repetição com falha por uma inventada.
- Limitar duração, corpus e memória; ter watchdog/timeout. Para pressão intensa, usar processo/contêiner com limite verificado e documentar efeitos do isolamento.
- Não provocar OOM global. Não exigir que haja swap ou thrashing: ausência também é resultado.
- Identificar limites de WSL/VM/contêiner e métricas que refletem host versus guest.

## 10. Métricas e formato dos resultados

| Categoria | Mínimo a registrar |
|---|---|
| Tempo | ingestão, recuperação, resposta, total, média, mediana, p95 e vazão |
| Memória | RSS, VSZ, MemAvailable, swap, cache e faltas de página disponíveis |
| Armazenamento | tamanho corpus/índice, bytes lidos/escritos, operações por segundo |
| Concorrência | processos, threads, fila média/máxima, espera e utilização de trabalhadores |
| Cache | hit rate, miss rate, tamanho, substituições, tempo economizado |
| Correção | itens perdidos/duplicados, integridade do log, ordem e falhas |
| Robustez | erros controlados, retentativas, recuperação e fila cheia/vazia |

Definir unidades e fontes. Separar E/S lógica da aplicação de E/S física observada: leituras servidas pelo cache de páginas podem não gerar leitura física. Separar faltas minor/major. Não somar RSS de processos sem discutir páginas compartilhadas. Threads de um processo compartilham o RSS.

Usar relógio monotônico para durações e horário civil com fuso para rastreabilidade. Calcular percentis por requisições, informando método e número de amostras; três repetições não substituem um conjunto suficiente de consultas. Apresentar variação entre repetições.

Fórmulas a documentar:

- Vazão = requisições concluídas / duração da janela de processamento.
- Hit rate = hits / (hits + misses); denominador zero deve ser tratado.
- Miss rate = misses / (hits + misses).
- Espera na fila = instante de retirada - instante de entrada.
- Utilização = tempo ocupado / tempo observado, com definição por trabalhador.
- Economia do cache: comparar execução pareada com cache desativado, ou indicar claramente quando for uma estimativa.

Cada execução deve salvar:

- `manifest.json`: run ID, commit/estado do código, versões, ambiente, data/fuso, comando, configuração, sementes, checksums, aquecimento, limites e status.
- `requests.csv` ou JSONL: ID, tempos por etapa, espera, hit/miss, resultado/erro e trabalhador.
- `resources.csv`: amostras com tempo, memória, CPU, fila, E/S e métricas disponíveis.
- `events.jsonl`: ingestão, consulta, recuperação, cache, geração, falha e encerramento.
- `summary.json`: métricas agregadas e contagem de consultas válidas/falhas.

Manter dados brutos imutáveis após análise. Scripts devem gerar tabelas/gráficos a partir deles, sem edição manual dos números.

## 11. Testes e evidências

Testar comportamentos relevantes:

- Determinismo de corpus, vetores e recuperação.
- Equivalência de conteúdo/resultados entre `read` e `mmap`.
- Limite de contexto e eviction do cache.
- Correção sob concorrência: IDs únicos, nenhum item perdido, logs parseáveis.
- Encerramento de fila e recuperação após arquivo ausente/fila saturada.
- Falha reproduzível sem proteção e ausência da duplicação com proteção.
- Agregação das métricas a partir de um conjunto pequeno com valores conhecidos.

Coletar evidências Linux de processos/threads, memória, armazenamento e chamadas de sistema. Sugestões: `ps`, `/proc`, `vmstat`, `iostat`, `/usr/bin/time -v` e `strace -f`. Usar tracing em execuções específicas, porque ele interfere no desempenho. Documentar comandos e interpretar as evidências; screenshots isoladas não substituem dados brutos.

## 12. Análise e gráficos

Produzir ao menos gráficos úteis para:

1. Tempo, RSS/VSZ e faltas de página: leitura convencional versus `mmap`.
2. Vazão, latência p95 e espera de fila por trabalhadores.
3. Tempo e hit rate por capacidade do cache/padrão de consulta.
4. Comportamento de memória sob corpus/contexto maior, quando executado.
5. Falha e correção de sincronização, usando tabela ou gráfico de duplicações/espera.

Mostrar unidades, parâmetros e dispersão entre repetições. Não concluir superioridade de uma técnica sem evidência. Explicar resultados inesperados.

Responder explicitamente às questões do enunciado: efeitos de corpus/índice/lote/contexto; diferenças de `mmap`; economia do cache; ganhos e contenção de concorrência; recursos compartilhados; falha demonstrada; mecanismo e trade-offs; paginação/swap/pressão; relação com RAG/embeddings/checkpoints; limites para modelos maiores, GPUs e sistemas distribuídos.

## 13. Relatório, apresentação e vídeo

### Relatório de 8 a 12 páginas, excluídos anexos

Incluir contribuição individual; introdução/problema; pergunta norteadora; ambiente; arquitetura; dados/corpus/embeddings/índice/cache; processos/threads/filas/recursos; sincronização; metodologia; resultados; memória/armazenamento/paginação/E/S; concorrência/cache/correção; relação com SO e IA generativa; limitações; conclusão e referências.

Preparar texto a partir das evidências reais. Ajustar distribuição de páginas após renderizar o PDF. Colocar logs extensos e comandos completos em anexos/repositório. Não preencher resultados pendentes com texto que pareça conclusão real.

### Apresentação oral

Planejar 10 a 12 minutos: problema, ambiente, arquitetura, dados/configurações, processos/recursos, experimentos, gráficos, falha/correção, memória/armazenamento, relação com IA e limitações. Distribuir falas entre todos; preparar demonstração curta com alternativa gravada caso o ambiente falhe.

### Vídeo

Até 20 minutos, todos participam. Mostrar aplicação, execução, evidências, experimentos, sincronização e interpretação. A equipe grava e valida acesso ao link. Colocar URL no README, no relatório e em `VIDEO.md` ou `video.txt`.

## 14. Entregas e reprodução

- [ ] Repositório público com nome validado pelo docente.
- [ ] Código executável, dependências e instruções suficientes.
- [ ] Dados sintéticos/gerador ou instruções de obtenção dos dados públicos.
- [ ] Logs, tabelas, gráficos, resultados brutos e evidências usadas na análise.
- [ ] Relatório PDF de 8 a 12 páginas, excluídos anexos.
- [ ] Tabela de contribuição individual verdadeira.
- [ ] Apresentação em PDF ou slides.
- [ ] Vídeo de até 20 minutos com todos e URL nos três locais exigidos.
- [ ] Materiais de terceiros atribuídos; limitações declaradas.
- [ ] Sem segredos, dados pessoais, documentos sigilosos ou pesos de modelos.
- [ ] Reprodução verificada a partir de clone limpo em Linux.

O README deve explicar instalação, ambiente, geração do corpus, ingestão, consulta, execução C1–C6, demonstração de corrida/correção, coleta, análise e localização das entregas. Criar modo rápido de validação e modo completo de experimentos. Informar duração e recursos estimados somente após observação ou como estimativa explícita.

## 15. Interface de comandos a implementar

Os comandos abaixo são um contrato sugerido, ainda não implementado. Ajustar e atualizar o README conforme a interface real.

```bash
python -m genresearch generate-corpus --config experiments/configs/corpus.json
python -m genresearch ingest --config experiments/configs/baseline.json
python -m genresearch query --text "consulta de exemplo" --config experiments/configs/baseline.json
python experiments/run_matrix.py --config experiments/configs/matrix.json --repetitions 3
python experiments/demonstrate_race.py
python experiments/analyze.py --input results/raw --output results
pytest
```

Todos os comandos publicados no README devem ser comandos reais testados, sem placeholders.

## 16. Cronograma sugerido

| Data | Meta |
|---|---|
| 10–11/10 | equipe, escopo, ambiente, dados e fundação |
| 12–14/10 | pipeline, métricas, concorrência, cache e sincronização |
| 15–16/10 | experimentos e repetições |
| 17–18/10 | análise, gráficos e relatório |
| 19/10 | slides, vídeo e reprodução |
| 20/10 | revisão e entrega até 23h59 |
| 21/10 | apresentação oral |

## 17. Primeiro pedido ao Codex

> Leia AGENTS.md e inspecione o repositório. Crie docs/status.md com os requisitos e etapas. Implemente primeiro a fundação e o pipeline sequencial com corpus sintético reproduzível, vetores determinísticos, armazenamento, recuperação, geração simulada documentada e métricas. Verifique o que puder no ambiente disponível e continue pelas etapas deste guia. Antes de experimentos maiores, defina limites adequados ao equipamento. Não invente resultados; registre tudo que depender de Linux ou de ação da equipe. Ao final de cada etapa, atualize o status e explique como reproduzir e compreender o trabalho.

## 18. Referências de orientação

- Enunciado acadêmico: `Atividade_2_Sistemas_Operacionais_2026_2_submetida.pdf` (4 páginas, fornecido pela equipe).
- Instruções de projeto para Codex: https://learn.chatgpt.com/docs/agent-configuration/agents-md

Adicionar referências técnicas realmente consultadas durante a implementação e análise, com links e versões quando relevantes.
