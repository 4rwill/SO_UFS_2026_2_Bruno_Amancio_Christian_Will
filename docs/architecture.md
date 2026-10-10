# Pipeline sequencial — etapa 2

Corpus sintético → fragmentação por caracteres → vetores SHA-256 → arquivos
persistidos → consulta vetorizada → cosseno/top-k → contexto UTF-8 limitado →
resposta simulada e métricas.

ingestion.py gera documentos; pipeline.py faz ingestão/consulta; retrieval.py
fragmenta e vetoriza; storage.py acessa arquivos; metrics.py salva artefatos;
cli.py expõe generate-corpus, ingest e query. Não há fila, cache ou trabalhadores
concorrentes nesta etapa.

Fragmentos têm até 256 caracteres, sobreposição de 32 e ID sequencial estável.
Vetores têm 64 dimensões: SHA-256 dos termos casefold determina o bucket; contagem
normalizada L2. Colisões são possíveis: trata-se de representação lexical simulada,
sem equivalência a embeddings semânticos de um modelo. Empates usam ID crescente.

corpus.bin concatena documentos; metadata.json registra offsets, origem, semente,
parâmetros, tamanhos e checksums; index.json contém fragmentos e vetores. O índice
JSON duplica os textos dos fragmentos para simplicidade e não é otimizado em RAM.
Destino publicado apenas após preparação; sobrescrita recusada. Checksums detectam
corpus de entrada alterado e arquivos persistidos corrompidos.

read e mmap acessam integralmente os mesmos corpus.bin/index.json. mmap copia
todos os bytes antes de fechar o mapeamento; não é uma implementação zero-copy.
Metadados são lidos convencionalmente nos dois modos. open_map_s mede abertura
e mapeamento dos dois arquivos; access_s mede acesso/cópia e fechamento;
loading_s inclui metadados, validação de SHA-256 e parse JSON. Bytes lógicos
incluem metadados; não são bytes físicos lidos do disco.

Recuperação usa cosseno, top-k=3 e contexto máximo de 512 bytes, contando separadores.
Truncamento respeita UTF-8; tokens aproximados = ceil(bytes/4), sem tokenizer real.
Trechos escolhidos, origem, offsets e scores são exportados. sleep de 0,01 s simula
espera e a resposta informa SHA-256 do contexto; não é geração de texto por IA.

Duracões usam time.monotonic. Artefatos têm UUID, comando, configuração, versão,
commit/estado, horário com fuso, sucesso/falha, tempos e resultado. resources.csv
tem amostras antes/depois (não pico): RSS/VSZ via /proc/self/status, memória
disponível via /proc/meminfo e faltas cumulativas minor/major via getrusage.
Indisponíveis são null; falhas são preservadas. Logs apenas start/fim nesta etapa;
eventos detalhados e proteção concorrente ficam para etapa 3. Percentis de uma
consulta têm n=1 e método nearest-rank, sem interpretação estatística.

Limites: entrada 1 MiB, índice 8 MiB, 2000 fragmentos no preset; teto validado
8 MiB de entrada, 32 MiB de índice, 5000 fragmentos, 512 dimensões. Ingestão
verifica timeout interno de 30 s entre documentos; os comandos publicados usam
watchdog externo de 60 s para limitar também parsing e consulta. Não são limites
rígidos de RSS. Pressão de memória não foi executada.
