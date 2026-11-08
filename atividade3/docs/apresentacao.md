# Roteiro de apresentação e vídeo

Apresentação com alvo de 11 minutos e vídeo com proposta de 15 minutos, a ajustar no ensaio. Todos devem compreender sua parte e participar de forma identificável. A distribuição de falas não comprova contribuição técnica efetiva. Os roteiros completos abaixo seguem os 11 slides atuais, com uma ficha por slide, nome completo do locutor, fala pronta, janela de tempo, miniatura e orientações de tela.

- [PDF das falas para a apresentação](../output/pdf/roteiro_apresentacao.pdf)
- [PDF das falas para o vídeo](../output/pdf/roteiro_video.pdf)
- [Texto editável da apresentação](roteiro_apresentacao.md)
- [Texto editável do vídeo](roteiro_video.md)
- [Slides em PDF usados como base](../output/slides/apresentacao_atividade3.pdf)
- [Fonte LaTeX Beamer da apresentação](../deliverables/apresentacao.tex)

O PDF da apresentação inclui respostas de apoio para as perguntas; o do vídeo inclui orientações de gravação. Ambos incluem instruções de operação da demonstração. Os slides 7 e 10 têm troca de locutor sem troca de slide. O slide 11 contém uma distribuição simulada de contribuições, detalhada em [contribuicoes.md](contribuicoes.md), e pendências. Conferir as atribuições com o trabalho efetivo antes da gravação/apresentação final.

Os tempos abaixo referem-se à apresentação. As janelas próprias do vídeo estão no seu roteiro. O fonte oficial dos slides agora é `deliverables/apresentacao.tex`. O comando `python atividade3/scripts/build_slides.py` compila o Beamer, confere os 11 títulos e a sequência, atualiza o hash do PDF no JSON de falas, renderiza miniaturas em `.build/roteiros/slides/` e regenera os dois roteiros.

Esse fluxo usa pdfLaTeX ou Tectonic, Poppler (`pdftoppm`) e os pacotes de `requirements-roteiros.txt`. Para atualizar somente as falas, editar `docs/roteiros_falas.json` e executar `python atividade3/scripts/build_roteiros.py`, mantendo as miniaturas atuais. Para recriar apenas as miniaturas, usar `python atividade3/scripts/render_roteiros_slides.py`. Os roteiros em PDF e Markdown são derivados do JSON; as falas e os tempos originais foram mantidos na conversão para Beamer.

| Slide | Tempo | Responsável sugerido | Conteúdo |
|---|---|---|---|
| 1. Laboratório e objetivo | 0:00-0:40 | Bruno | Pergunta norteadora e recorte próprio sem kit |
| 2. Ambiente e camadas | 0:40-1:40 | Iasmin | Host Windows, virtualização WSL2, kernel compartilhado, daemon e imagens |
| 3. Evidências de namespaces | 1:40-2:50 | Pedro | Handles PID/mount/network e dois PIDs 1 internos |
| 4. Carga e protocolo | 2:50-4:00 | Christian | 20 milhões de iterações, oráculo, piloto e alternância |
| 5. Limites efetivos | 4:00-5:00 | Marcos | cpu.max, memória, swap e tarefas; quota por período |
| 6. Seis medições | 5:00-6:20 | Sibele | Gráfico com seis observações e medianas 7,074/3,384 s |
| 7. Throttling e memória | 6:20-7:20 | Marcos e Sibele | Deltas de cpu.stat e escopos distintos da memória |
| 8. Mount e menor privilégio | 7:20-8:30 | Silas | Leitura, EROFS, UID 65534, capabilities e NoNewPrivs |
| 9. Evidência selecionada | 8:30-9:30 | Christian | Executar auditor ou abrir registro bruto antes preparado |
| 10. Limitações e relação com IA | 9:30-10:30 | Silas e Iasmin | Ruído do host, ancestrais não visíveis e aplicação a servidor compartilhado |
| 11. Contribuições e encerramento | 10:30-11:00 | Bruno e equipe | Contribuições reais após revisão, declaração de IA e conclusão |

## Demonstração selecionada

Preparar o terminal antes da apresentação, na raiz do repositório, com Python configurado:

```bash
python atividade3/scripts/audit.py atividade3/results/raw/20261108T013949Z-19921f7f
```

Mostrar que o auditor verifica seis registros, checksums independentes, limites efetivos e limpeza. Abrir C1-1.json para apontar cpu.max e cpu_stat_delta. O mount-readonly.json contém a evidência negativa real. Não consumir o tempo com instalação, download ou coleta integral. A reprodução ao vivo do mount deve ser feita apenas após ensaio; o laboratório completo gera um novo lote.

## Perguntas prováveis

- **Por que ambos têm PID 1?** Cada PID namespace possui sua própria numeração; o Docker informou PIDs diferentes no host do daemon.
- **Contêiner é VM?** Neste ambiente há virtualização Linux no WSL2, e os contêineres compartilham o kernel Linux dessa infraestrutura.
- **0,5 CPU significa meio núcleo reservado?** É um teto de tempo agregado por período; não define afinidade nem reserva.
- **Por que o ganho não foi exatamente 2?** Existem três observações por condição e interferência não isolada do host/escalonamento/frequência.
- **As flags provam o limite?** O roteiro confere cpu.max, memory.max, memory.swap.max e pids.max antes/depois.
- **Por que memory.current difere de RSS?** Cgroup e processo têm escopos e contabilização diferentes; memory.peak ainda cobre toda a vida do grupo.
- **A escrita negada prova segurança total?** Comprova a restrição daquele mount; kernel e runtime permanecem compartilhados.
- **Os ancestrais estavam sem limites?** Não foi possível confirmá-los pela visão externa disponível. A limitação está documentada.

## Pendências para gravação e entrega

Revisar o conteúdo, confirmar a divisão e contribuição efetiva, ensaiar com cronômetro e gravar todos de forma identificável. Conferir qualidade de áudio e legibilidade dos comandos. Publicar o vídeo com acesso adequado ao docente e inserir a URL em VIDEO.md, README e relatório. Registrar o commit final e submeter até 10/11/2026. O vídeo não substitui a apresentação em 11/11/2026.
