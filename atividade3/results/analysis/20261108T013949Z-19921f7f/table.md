# Resultados da Atividade 3

Três repetições por condição; variação = mínimo–máximo. Piloto excluído.

| Condição | Quota (CPU) | n | Wall mediano (s) | Mín.–máx. (s) | CPU mediana (s) | Trabalho mediano (iterações/s) |
|---|---:|---:|---:|---:|---:|---:|
| C1 | 0.5 | 3 | 7.0739 | 6.3852–8.2050 | 3.5227 | 2827285 |
| C2 | 1.0 | 3 | 3.3840 | 3.2737–3.4952 | 3.3829 | 5910140 |

Razão entre medianas de wall (C1/C2): 2.090×.

Wall mede somente o trabalho; CPU é tempo do processo. Trabalho/s não é tokens/s.
RSS máximo é do processo; memory.current são dois snapshots do grupo; memory.peak cobre a vida do cgroup.
Não há inferência estatística nem medição de VRAM ou isolamento absoluto.
