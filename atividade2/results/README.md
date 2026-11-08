# Resultados e evidências da Atividade 2

## Conjunto principal usado na análise

| Artefato | Caminho relativo a `results/` |
|---|---|
| Matriz final, 11 condições × 3 repetições | `raw/matrix/15c7fb31a435409597342b40f0d70665/` |
| Auditoria da matriz | `evidence/matrix-final/` |
| Tabelas por execução e agregações | `summary/matrix-15c7fb31/` |
| Cinco gráficos PNG/SVG, diagnósticos e proveniência | `analysis/matrix-15c7fb31/` |
| Demonstração isolada de corrida/correção | `raw/stage4/7309c1af68234c8aa1f17d02d92f4737/` |
| Saída e testes da demonstração | `evidence/stage4-validation/` |
| Inventário experimental | `evidence/stage1-environment/` |
| Processos/threads/syscalls e monitores | `evidence/linux-tracing-20261010/` |
| Auditoria da coleta complementar | `summary/linux-tracing-20261010-verified/` |
| Validações de equivalência e robustez | `evidence/stage2-final/` e `evidence/stage3-check/` |

As demais pastas contêm ensaios e validações anteriores, preservados como histórico de evidências. Não se agregam ao lote final e não substituem os caminhos acima. Não editar os dados brutos nem seus manifestos para atualizar caminhos, versões ou autoria.

O lote principal contém 720 conclusões e 72 falhas intencionais, sem perdas/duplicações de IDs. A coleta complementar usou outra espera simulada e tracing: seus tempos não se misturam à matriz. Valores `null` representam métricas indisponíveis.

Os artefatos por execução são `manifest.json`, `requests.jsonl`, `resources.csv`, `events.jsonl` e `summary.json`. Comandos de auditoria e reprodução no [README](../README.md); interpretação em [docs/analysis.md](../docs/analysis.md).
