# Organização e reprodução após a mudança de pasta

Em 08/11/2026, o material da Atividade 2 foi reunido em `atividade2/`: código, testes, configurações, dados, resultados, documentação e fonte do relatório. Os arquivos de evidência foram movidos preservando seus bytes. As referências históricas a comandos, commits e caminhos nas medições não foram reescritas.

## Diretório de execução

Os caminhos `src/`, `experiments/`, `data/`, `results/` e demais caminhos registrados são relativos à raiz da **atividade**, agora `atividade2/`. Antes dos comandos documentados no README e nos textos históricos:

```bash
cd atividade2
export PYTHONPATH=src:.
```

A configuração do pacote também está em `atividade2/pyproject.toml`. Uma instalação a partir da raiz do repositório pode apontar para `./atividade2`; a execução por PYTHONPATH dispensa a instalação.

## Conferência dos dados publicados

Dentro de `atividade2/`, com o ambiente Python e dependências de análise disponíveis:

```bash
python -m unittest discover -s tests -v
python scripts/verify_matrix.py results/raw/matrix/15c7fb31a435409597342b40f0d70665
python scripts/verify_analysis.py results/analysis/matrix-15c7fb31
```

As ferramentas continuam encontrando os caminhos relativos históricos a partir dessa pasta. Não é necessário alterar os JSON/JSONL, CSV ou os hashes de proveniência. Os dados gerados em `data/generated/`, ambientes virtuais e validações locais continuam fora do versionamento.

A Atividade 3 permanece em `../atividade3/` e seus comandos partem da raiz do repositório, conforme seu próprio README.
