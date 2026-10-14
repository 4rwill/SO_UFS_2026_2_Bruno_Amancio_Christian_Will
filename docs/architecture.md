# Arquitetura do GenResearch-Servidor

Aplicação local de terminal, com corpus sintético, vetores lexicais simulados, persistência em arquivos, recuperação top-k, resposta de espera simulada, fila limitada e cache compartilhado. `serve` executa uma carga finita: não há HTTP, LLM ou GPU.

```text
Documentos sintéticos -> fragmentação -> vetores -> corpus/índice/metadados
Consultas -> produtores -> Queue limitada -> consumidores -> cache
  miss -> leitura/validação -> recuperação -> contexto -> resposta -> cache
  hit/coalesced -> reutilização do resultado
  todos os caminhos -> métricas, eventos JSONL e resultado/erro explícito
```

## Componentes

| Módulo em `src/genresearch/` | Responsabilidade |
|---|---|
| `cli.py` | Comandos `generate-corpus`, `ingest`, `query` e `serve` |
| `ingestion.py` | Corpus sintético determinístico e manifesto |
| `pipeline.py` | Ingestão, carregamento, recuperação e resposta |
| `retrieval.py` | Fragmentação, vetores e similaridade |
| `storage.py` | Checksums, leitura convencional e mmap |
| `server.py` | Produtores/consumidores, fila, métricas e encerramento |
| `cache.py` | LRU e single-flight com lock/Event por chave |
| `logging_setup.py` | Escrita concorrente protegida de eventos |
| `metrics.py` | Artefatos e observação de recursos |

## Corpus, índice e recuperação

Fragmentos de até 256 caracteres, sobreposição 32 e IDs estáveis. Vetores de 64 dimensões usam SHA-256 dos termos casefold para determinar buckets e normalização L2 das contagens. Colisões são possíveis: a representação é lexical, sem equivalência a embeddings semânticos de um modelo. Cosseno determina top-k, com desempate por ID.

`corpus.bin` concatena documentos; `metadata.json` registra origem, offsets, semente, parâmetros, tamanhos e checksums; `index.json` contém fragmentos e vetores. O JSON duplica texto e é parte do custo medido. Arquivos permanecem imutáveis durante uma execução; corrupção e mudanças de versão são rejeitadas.

A linha de base usa top-k=3, contexto máximo de 512 bytes, truncamento UTF-8 e tokens apenas aproximados por `ceil(bytes/4)`. A resposta informa SHA-256 do contexto e usa `sleep` de 0,01 s para simular espera, sem geração textual por IA.

## read e mmap

Os dois modos acessam integralmente os mesmos `corpus.bin` e `index.json`; os metadados são lidos convencionalmente. O modo mmap copia todos os bytes antes de fechar o mapeamento: não é zero-copy. `open_map_s` mede abertura/mapeamento; `access_s`, acesso/cópia/fechamento; `loading_s` inclui metadados, checksums e parsing JSON. Bytes lógicos não representam bytes físicos de disco.

## Concorrência e observabilidade

Dois produtores e consumidores configuráveis compartilham fila, cache e log dentro de um processo. O cache coordena cálculos em andamento; o log serializa linhas JSONL. O pipeline reabre/valida arquivos em cada cálculo, sem índice residente compartilhado. RSS é do processo e não deve ser somado por thread.

Cada execução produz manifesto, requisições, recursos, eventos e resumo. Configurações, IDs e falhas explícitas permitem verificar perdas, duplicações e encerramento. Definições completas em [concurrency.md](concurrency.md); a falha isolada e sua correção estão em [synchronization.md](synchronization.md).
