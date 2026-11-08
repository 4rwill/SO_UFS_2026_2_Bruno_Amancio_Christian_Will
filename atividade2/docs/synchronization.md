# Sincronização — duplicação de trabalho e correção

Executável isolado: experiments/demonstrate_race.py. A aplicação normal não
importa este módulo e continua usando SharedCache protegido. Não há modo inseguro
em serve. A demonstração usa duas threads e uma chave comum; conteúdo/retorno
são sintéticos e o custo usa sleep de 0,02 s (espera, não carga de CPU ou modelo).

## Falha reproduzível

As duas threads começam com cache vazio. Cada uma observa miss, registra o evento
e aguarda uma Barrier fora de qualquer lock. Só após ambas observarem miss,
podem calcular e atualizar o dicionário. São dois cálculos e uma entrada final:
a atribuição parece correta, mas houve duplicação de trabalho. Locks do contador
e do log protegem somente as evidências e não corrigem a decisão do cache.

## Correção

Reutiliza SharedCache da execução normal. O lock cobre busca e criação de uma
chave pending. Um owner calcula fora do lock; o seguidor aguarda o Event dessa
chave. O owner publica resultado/erro e sinaliza; falhas não são cacheadas.
Para garantir que o seguidor exerça esse caminho, o owner da demonstração espera
observar um coalesced com timeout, fora do lock. Essa espera é instrumentação do
experimento e não existe no servidor normal. Não há barreira dentro de lock.

Assim, uma atribuição protegida isoladamente não seria suficiente: é necessário
coordenar decisão, cálculo em andamento e publicação. O custo é bookkeeping,
lock curto, Event e espera dos seguidores; erro do owner afeta quem aguarda,
mas permite retentativa. Um lock global mantido durante o cálculo bloquearia
chaves independentes; single-flight restringe a espera à mesma chave.

## Isolamento e evidências

Cada versão executa em processo spawn separado. Pai aguarda até 5 s, termina o
filho se necessário, usa kill como último recurso e confirma encerramento.
Barreiras/espera por chave têm timeout de 2 s. O comando foi executado também
com watchdog externo de 15 s. Nenhum deadlock foi provocado nesta etapa.
Timeout/falha de filho registra calculations=null; não é convertido em zero.

Runs UUID em results/raw/stage4 salvam manifest.json, summary.json,
workers.jsonl, unsafe-events.jsonl e corrected-events.jsonl. Cada evento contém
sequência, relógio monotônico e horário civil UTC com fuso; manifesto registra
versões, commit/estado, comando, parâmetros e status. Resultados são preservados.

## Resultado real observado no WSL

Run 7309c1af68234c8aa1f17d02d92f4737, Python 3.14.4, Ubuntu/WSL 2;
saída CLI em results/evidence/stage4-validation/demo.json.

| Versão | Cálculos | Cálculos duplicados | Entradas finais | Resultados iguais |
|---|---:|---:|---:|---|
| Sem coordenação | 2 | 1 | 1 | Sim |
| SharedCache/single-flight | 1 | 0 | 1 | Sim |

No run corrigido, um trabalhador foi miss/owner e o outro coalesced; hits=0,
misses=2 porque ambos chegaram antes de existir resultado pronto. O seguidor
observou cerca de 0,02194 s entre lookup e resultado. Esse valor inclui espera,
logging/escalonamento e cópia, não é uma medida exclusiva de tempo de lock.
coordination_overhead_s = lookup_to_result_s − own_compute_s, limitada a zero
para erro de arredondamento; inclui barreira/logging e não isola contenção de mutex.
own_compute_s inclui a espera de instrumentação no owner corrigido. Não comparar
essas durações como benchmark imparcial: as duas versões usam controles diferentes
para tornar os caminhos reproduzíveis. A evidência principal é a contagem 2 → 1.

As duas versões finalizaram com exit code 0, nenhum processo filho ou trabalhador
vivo e resultados iguais. 17 testes passaram, incluindo verificação dos dois
misses antes de qualquer cálculo inseguro e encerramento pelo watchdog.
Testes em results/evidence/stage4-validation/tests.txt. Esta demonstração atende
à Parte D; resultados da matriz C1–C6 e limites de desempenho em docs/analysis.md.
