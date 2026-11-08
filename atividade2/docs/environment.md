# Ambiente verificado — Parte A

Coleta: 10/10/2026 às 15:44:59 -03:00 (America/Sao_Paulo).
Fontes brutas: results/evidence/stage1-environment.

| Item | Observação e fonte |
|---|---|
| Sistema | Ubuntu 26.04.1 LTS, os-release.txt |
| Execução | WSL 2 sobre Windows, execution-mode.txt e wsl --list --verbose |
| Kernel | 6.18.40.1-microsoft-standard-WSL2, uname.txt |
| CPU | Intel Core i5-11260H, 6 núcleos/12 CPUs lógicas visíveis, lscpu.txt |
| RAM guest | 3,7 GiB; disponível 3,1 GiB na coleta, free.txt/meminfo.txt |
| Swap guest | 1 GiB; 0 B usados no instante observado, free.txt/swap.txt |
| Disco projeto | C: via /mnt/c, 9p/DrvFS; 476 GiB total, 323 GiB disponíveis, df.txt/filesystem.txt |
| Disco Linux | /dev/sdd, ext4, volume virtual, 1007 GiB apresentados, df.txt |
| GPU host exposta | NVIDIA GeForce GTX 1650, 4096 MiB VRAM, nvidia.txt |
| Python | 3.14.4, python.txt |
| Venv | /home/will/.venvs/genresearch; pip 25.1.1, tooling.txt |
| Bibliotecas aplicação | Biblioteca padrão; pip freeze vazio, libraries.txt |
| Ferramentas | sysstat 12.7.7-0ubuntu2; pciutils 1:3.14.0-1build2, tool-versions.txt |
| Aplicação | GenResearch 0.1.0; corpus sintético; sem modelo de inferência |
| Assistência | Codex; modelo identificado pela sessão como GPT-6 |
| Código | e649deb2855910f8aa890bb6858d7fb744e5ce8c, com alterações, commit.txt/git-state.txt |

O tamanho aparente do volume virtual Linux não é reserva garantida no host.
RAM/swap e dispositivos do guest não descrevem todo o Windows. GPU não é usada.
E/S em /mnt/c passa pela integração Windows: manter mesmo sistema de arquivos
nas comparações e declarar essa limitação. Testes usam temporários Linux.
vmstat/iostat foram executados por 5 s e encerrados por timeout (124); todos os
demais comandos retornaram 0. São observações do ambiente, sem carga RAG.
