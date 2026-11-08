# Sistemas Operacionais - UFS 2026.2

Repositório das atividades da equipe GenResearch, organizado por atividade.

| Atividade | Conteúdo | Guia |
|---|---|---|
| Atividade 2 | Pipeline GenResearch, memória, armazenamento, filas, cache e sincronização | [atividade2/README.md](atividade2/README.md) |
| Atividade 3 | Laboratório de contêineres, namespaces, quotas de CPU, cgroups e montagem somente leitura | [atividade3/README.md](atividade3/README.md) |

## Atividade 2

Código, configurações, testes, documentação, fonte do relatório e resultados históricos estão em `atividade2/`. Execute seus comandos **dentro dessa pasta**, para conservar os caminhos relativos registrados nas configurações e evidências:

```bash
cd atividade2
export PYTHONPATH=src:.
python -m unittest discover -s tests -v
```

Veja a [organização e reprodução](atividade2/docs/organization.md) e o [guia completo](atividade2/README.md).

## Atividade 3

Scripts próprios, seis execuções reais auditadas, CSV, gráfico, relatório e apresentação estão em `atividade3/`. Seus comandos continuam sendo executados a partir da **raiz do repositório**:

```bash
python atividade3/scripts/audit.py atividade3/results/raw/20261108T013949Z-19921f7f
python -m unittest discover -s atividade3/tests -v
```

- [Relatório PDF para revisão](atividade3/output/pdf/relatorio_atividade3.pdf)
- [Apresentação em PDF](atividade3/output/slides/apresentacao_atividade3.pdf)
- [Fonte LaTeX Beamer dos slides](atividade3/deliverables/apresentacao.tex)
- [Dados, CSV e gráfico](atividade3/results/analysis/20261108T013949Z-19921f7f/)
- [Situação dos requisitos e pendências da equipe](atividade3/docs/status.md)

[Vídeo da Atividade 3 no Google Drive](https://drive.google.com/drive/folders/1yPalBhHtxjZmD2yZngRQVawkAElJC-Hj?usp=sharing). A equipe deve conferir o acesso à gravação e efetuar a submissão acadêmica. A publicação do código não comprova a entrega no Classroom.

Ambientes virtuais, temporários e materiais locais de outra disciplina ficam ignorados pelo Git e não fazem parte das atividades publicadas.
