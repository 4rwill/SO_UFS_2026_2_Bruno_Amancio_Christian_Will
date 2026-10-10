# Fundação e protocolo pendente

MemFree é memória atualmente livre; MemAvailable estima memória utilizável por
novas cargas, incluindo partes recuperáveis de caches. O cache de páginas mantém
conteúdo de arquivos em RAM: uma leitura lógica pode dispensar E/S física. Swap
armazena páginas fora da RAM; sua ausência deve ser registrada, não tratada como
falha. A coleta Linux inicial está documentada em docs/environment.md.
Cache de páginas é útil porque evita releituras físicas e pode ser recuperado;
não representa necessariamente memória desperdiçada. Paginação move e mapeia
páginas conforme a demanda: datasets, índices, embeddings e checkpoints grandes
podem exigir acesso a disco quando as páginas necessárias não estão residentes.
Isso será investigado nas próximas etapas, sem conclusão experimental antecipada.

O gerador usa apenas biblioteca padrão e não usa hash() nativo. Limites atuais:
1000 documentos, 1000 frases/documento, 8 MiB de texto no máximo, 30 segundos e
reserva de disco de limite + 1 MiB. O preset inicial limita texto a 1 MiB. Esses
limites são conservadores para validação funcional; não autorizam pressão de
memória. Antes de C5, medir RAM, MemAvailable e disco no Linux e definir orçamento
de processo/contêiner e watchdog. Não alterar swap nem limpar caches do kernel.

A coleta registra saídas e códigos, inclusive comandos ausentes. Código 124 dos
monitores significa encerramento por timeout; códigos diferentes exigem inspeção.
GPU, VRAM e WSL 2 foram registrados em docs/environment.md. Os testes Windows
e a coleta básica Linux não constituem comparação experimental C1–C6.

Próximas etapas: separar aquecimento, executar processos novos, pelo menos três
repetições válidas por configuração, definir consultas/ordem/limites previamente,
salvar manifest, requests, resources, events e summary por execução. Dados brutos
devem permanecer imutáveis e indisponibilidade deve ser null, nunca zero fictício.

Assistência: a fundação foi preparada com Codex em 10/10/2026, segundo AGENTS.md.
A equipe deve revisar e declarar esse uso conforme as regras institucionais.
