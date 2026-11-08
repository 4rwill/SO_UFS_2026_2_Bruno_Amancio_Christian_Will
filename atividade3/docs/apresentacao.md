# Apresentação e vídeo

Os 14 slides usam LaTeX Beamer 16:9, tema Madrid, faixa azul, rodapé da disciplina e nome completo de quem apresenta. A apresentação tem alvo de 11 minutos, com perguntas separadas de 3-5 minutos; o roteiro de vídeo propõe 15 minutos. Os tempos devem ser ajustados no ensaio.

## Ordem dos apresentadores

Cada pessoa conclui seu bloco de dois slides antes da próxima assumir. Não há slides compartilhados nem retorno de quem já concluiu sua parte.

| Integrante | Slides | Janela na apresentação | Tema |
|---|---|---|---|
| Bruno Amancio Ferreira | 1-2 | 00:00-01:25 | Abertura, objetivo, organização e percurso do laboratório |
| Iasmin Victoria Teixeira Barreto | 3-4 | 01:25-03:00 | Ambiente Windows/WSL2/Docker, diagrama e protocolo experimental |
| Pedro César Figueiredo Carneiro | 5-6 | 03:00-04:30 | Namespaces PID, mount e network; numeração dos processos |
| Christian Will Silva Santos Nunes | 7-8 | 04:30-06:15 | Carga determinística, checksum, auditoria e demonstração |
| Marcos Vinícius Dantas Aguiar | 9-10 | 06:15-07:45 | Limites efetivos do cgroup v2, quotas e throttling |
| Sibele Oliveira Cruz | 11-12 | 07:45-09:25 | Seis medições, medianas, gráficos e escopos de memória |
| Silas Santos da Silva | 13-14 | 09:25-11:00 | Montagem read-only, menor privilégio, limitações e conclusão |

As trocas acontecem entre os slides 2/3, 4/5, 6/7, 8/9, 10/11 e 12/13. Silas encerra a exposição no slide 14.

## Materiais

- [Apresentação em PDF](../output/slides/apresentacao_atividade3.pdf).
- [Fonte LaTeX Beamer](../deliverables/apresentacao.tex).
- [Falas para a apresentação em PDF](../output/pdf/roteiro_apresentacao.pdf).
- [Falas para o vídeo em PDF](../output/pdf/roteiro_video.pdf).
- [Texto editável da apresentação](roteiro_apresentacao.md).
- [Texto editável do vídeo](roteiro_video.md).
- [Vídeo no Google Drive](https://drive.google.com/drive/folders/1yPalBhHtxjZmD2yZngRQVawkAElJC-Hj?usp=sharing).

## Compilação e sincronização

Editar o conteúdo visual em `deliverables/apresentacao.tex` e as falas em `docs/roteiros_falas.json`. O comando abaixo compila, confere títulos e apresentadores, atualiza o hash do PDF, renderiza as miniaturas e regenera os dois roteiros:

```bash
python atividade3/scripts/build_slides.py
```

Usar pdfLaTeX ou Tectonic, Poppler (`pdftoppm`) e os pacotes de `requirements-roteiros.txt`. Para compilar apenas os slides, usar `--skip-roteiros`. No Overleaf, selecionar pdfLaTeX; o fonte é autossuficiente. Para ensaiar com as notas no Beamer, trocar `\notasfalse` por `\notastrue`; a versão para projeção mantém as notas ocultas.

Para atualizar somente os roteiros, usar `python atividade3/scripts/build_roteiros.py`. Para recriar somente as miniaturas, usar `python atividade3/scripts/render_roteiros_slides.py`.

## Demonstração no slide 8

Christian mostra a auditoria dos arquivos já coletados. Preparar o terminal na raiz do repositório:

```bash
python atividade3/scripts/audit.py atividade3/results/raw/20261108T013949Z-19921f7f
```

Na apresentação, apontar `valid=true`, `main_runs=6` e `verified_files=68`. Abrir `runs/C1-1.json` para conferir N, checksum, `cpu.max` e `cpu_stat_delta`. A auditoria não repete as seis medições. Se o comando atual falhar, explicar e recorrer aos arquivos preservados; seguir para o slide 9 com Marcos.

**No vídeo, Christian mostra somente o repositório, sem executar comandos.** Preparar as abas `manifest.json`, `runs/C1-1.json`, `mount-readonly.json` e `SHA256SUMS.json` do lote. No manifesto, mostrar `status=completed`, `valid_main_runs=6` e `cleanup_confirmed=true`; depois, percorrer os campos de C1-1, a escrita negada e a lista de hashes. Na seção `cpu_stat_delta`, os valores são deltas (71 e 3544785), distintos dos contadores absolutos. A navegação apresenta registros existentes e não equivale a uma nova execução do auditor. A fala completa está no roteiro do vídeo, entre 07:00 e 08:30.

## Conferência da entrega

Conferir áudio, legibilidade, identificação dos participantes e acesso externo ao vídeo. O link informado é de uma pasta do Google Drive; verificar se o docente consegue localizar e abrir a gravação. A submissão no Classroom e seu comprovante são responsabilidade da equipe. Entrega em 10/11/2026 e apresentação em 11/11/2026.
