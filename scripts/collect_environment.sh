#!/usr/bin/env bash
# Uso: bash scripts/collect_environment.sh DIRETORIO_NOVO [SEGUNDOS]
set -euo pipefail
export TZ=America/Sao_Paulo
python_bin=${GENRESEARCH_PYTHON:-python3}
if [[ $(uname -s) != Linux ]]; then
  echo 'A coleta exige Linux.' >&2
  exit 1
fi
out=${1:-results/evidence/environment-$(date +%Y%m%dT%H%M%S%z)}
seconds=${2:-5}
if [[ ! $seconds =~ ^[0-9]+$ ]] || (( seconds < 1 || seconds > 60 )); then
  echo 'Duração deve ser inteira entre 1 e 60 segundos.' >&2
  exit 1
fi
command -v timeout >/dev/null || { echo 'timeout é necessário.' >&2; exit 1; }
if [[ -e $out ]]; then echo 'Destino já existe.' >&2; exit 1; fi
mkdir -p "$out"
collect() {
  local name=$1
  shift
  local code=0
  local limit=10
  if [[ $name == vmstat || $name == iostat ]]; then limit=$((seconds + 2)); fi
  timeout "$limit" "$@" >"$out/$name.txt" 2>&1 || code=$?
  printf '%s\t%s\n' "$name" "$code" >>"$out/status.tsv"
}
printf 'command\texit_code\n' >"$out/status.tsv"
collect date date --iso-8601=seconds
collect uname uname -a
collect os-release cat /etc/os-release
collect lscpu lscpu
collect free free -h
collect meminfo cat /proc/meminfo
collect lsblk lsblk -f
collect df df -hT
collect swap swapon --show
collect python "$python_bin" --version
collect libraries "$python_bin" -m pip freeze
collect tooling "$python_bin" -m pip --version
# Exceção limitada a esta chamada e a este checkout compartilhado com Windows.
collect commit git -c "safe.directory=$PWD" rev-parse HEAD
collect git-state git -c "safe.directory=$PWD" status --short
collect filesystem findmnt -T "$PWD"
collect tool-versions dpkg-query -W python3 python3-venv sysstat pciutils
collect gpu lspci
collect nvidia nvidia-smi
collect execution-mode systemd-detect-virt
# timeout=124 é o término previsto dos monitores, não uma medição zero.
collect vmstat timeout "$seconds" vmstat 1
collect iostat timeout "$seconds" iostat -xz 1
echo "Coleta salva em $out; interprete os códigos em status.tsv."
