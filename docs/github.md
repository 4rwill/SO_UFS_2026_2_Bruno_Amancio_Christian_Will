# Arquivos preparados para o GitHub

## Incluídos

- Código em src, testes, scripts e experimentos/configurações.
- README, AGENTS.md e documentação em docs, incluindo o roteiro overview.md.
- pyproject.toml e dependências de análise com versões testadas.
- data/README.md: origem sintética e instruções de geração.
- results/raw, evidence, summary e analysis: medições reais, testes, auditorias,
  tabelas e gráficos que sustentam a análise. Ensaios iniciais/falhas permanecem
  identificados; não misturar esses lotes com o final.

Resultados existentes ocupam aproximadamente 14 MiB; maior arquivo observado
é um trace de aproximadamente 1,1 MB. Não foi necessário retirar evidências
por tamanho. .gitattributes impede conversão de quebras de linha em results,
preservando os bytes utilizados pelos checksums.

## Excluídos, preservados no computador

Venvs, caches Python, corpus/índices gerados em data/generated, arquivos .env,
artefatos de build, configurações locais de editores e chaves privadas comuns.
planejamento-qualidade pertence a outra atividade e foi excluído deste repositório.
Nenhum arquivo dessa pasta foi movido ou apagado. O PDF do enunciado externo
ao checkout não foi copiado para publicação.

Dados de ambiente contêm caminhos históricos, PIDs, características do equipamento
e versões necessários à rastreabilidade. Caminhos do computador original não
devem ser usados como instruções universais de instalação. Dados brutos não foram
reescritos para mudar seus caminhos. A busca por padrões comuns de credenciais
não encontrou ocorrências; isso é uma checagem limitada, não garantia absoluta.

## Continuidade após clonar

O corpus e os índices devem ser recriados antes de consultar. Na raiz, com Python
Linux e PYTHONPATH=src configurados, a ordem é generate-corpus usando
experiments/configs/corpus-linux.json, depois ingest usando baseline.json.
Os comandos e parâmetros estão no README. Ajustar caminho do checkout e do venv
ao equipamento de cada integrante; as configurações usam caminhos relativos.
Não afirmar reprodução em clone limpo: essa validação continua pendente.

Relatório, slides, vídeo e contribuições humanas ainda dependem da equipe.
Não foram criados materiais fictícios para preencher essas entregas.

## Revisão do commit

Os arquivos selecionados foram adicionados ao índice Git (staging). Antes de
criar o commit, revisar git diff --cached --stat e git diff --cached.
Não foi criado commit nem realizado push nesta preparação.
Conferência do staging: 1012 arquivos selecionados, incluindo 955 arquivos de
resultados com bytes idênticos aos originais; exclusões locais verificadas.
Espaçamento original dos logs/CSV não foi corrigido, para preservar evidências.
