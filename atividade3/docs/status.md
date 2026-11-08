# Situação da Atividade 3

Atualização: 08/11/2026, America/Sao_Paulo. Entrega em 10/11/2026; apresentação em 11/11/2026.

| Requisito | Estado | Evidência / próximo passo |
|---|---|---|
| Implementação sem kit | Implementado e executado | scripts/ e snapshots source/ do lote |
| Ambiente Linux/Docker e imagem por digest | Verificado | docker-environment.json, linux-environment.json, image.lock.json |
| Host físico e distribuição do daemon | Verificado | results/evidence/host-20261108T014504Z/environment.json |
| Diagrama das camadas | Preparado | Relatório e slides |
| Dois contêineres e PID/mount/network | Verificado | namespaces.json; PIDs 567/612 do host do daemon, ambos internos 1 |
| Piloto e N congelado | Verificado | runs/pilot-0.json, manifest.json, N=20000000 |
| Seis execuções alternadas e corretas | Verificado | runs/C1-1 a C2-3; 68 hashes auditados |
| Quotas CPU, memória, swap e tarefas | Verificado | cpu.max, memory.max, memory.swap.max e pids.max antes/depois |
| Limites ancestrais externos | Não confirmados | PID de inspect invisível no /proc acessível via WSL; limitação documentada |
| CPU/wall, throttling e memória | Verificado | Registros brutos, runs.csv e relatório |
| Leitura e escrita negada read-only | Verificado | mount-readonly.json, errno 30, UID 65534, CapEff zero, NoNewPrivs 1 |
| CSV, tabela e gráfico | Gerado e inspecionado | results/analysis/20261108T013949Z-19921f7f |
| Auditor e testes negativos | Verificado | Seis testes passaram no Ubuntu; resultados em results/evidence/tests.txt |
| Limpeza dos contêineres | Confirmada | Manifesto do lote e logs do coletor complementar |
| Relatório e slides | Preparados para revisão | Fontes LaTeX em deliverables/relatorio.tex e apresentacao.tex (Beamer); PDFs em output/pdf e output/slides |
| Falas completas para vídeo e apresentação | Preparadas para ensaio | output/pdf/roteiro_video.pdf e roteiro_apresentacao.pdf; miniaturas sincronizadas com o Beamer, falas por aluno, 14 slides e tempos estimados |
| Declaração de IA | Preparada para revisão | docs/uso_ia.md; modelo exato a confirmar se disponível |
| Participação na apresentação | Definida | docs/contribuicoes.md; sete blocos contínuos de dois slides, um apresentador por slide |
| Vídeo e URL | Link registrado | VIDEO.md, README, relatório e slide 14; pasta do Drive fornecida pela equipe, acesso externo a conferir |
| Ensaio e apresentação de todos | Manual, pendente | docs/apresentacao.md |
| Commit de referência | Registrado | a8347f78e9da9f34818df77b3e50d8d560ea7568; versão revisada dos materiais, indicada no relatório |
| Submissão | Manual, pendente | Equipe deve submeter e guardar comprovante |

Não houve falhas nas seis cargas principais. Tentativas auxiliares com erro foram preservadas: testes Windows restritos e primeira busca de ancestrais. Elas não foram contadas como medições principais nem apagadas.
