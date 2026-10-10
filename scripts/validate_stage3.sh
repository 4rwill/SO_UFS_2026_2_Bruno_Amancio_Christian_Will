#!/usr/bin/env bash
set -euo pipefail
python_bin=${GENRESEARCH_PYTHON:-python3}
out=${1:-results/evidence/stage3-check}
if [[ -e $out ]]; then echo 'Destino já existe.' >&2; exit 1; fi
mkdir -p "$out"
export PYTHONPATH=src
timeout 60 "$python_bin" -m unittest discover -s tests -v >"$out/tests.txt" 2>&1
timeout 30 "$python_bin" -m genresearch serve --config experiments/configs/concurrent.json >"$out/serve.json"
for scenario in failure saturation; do
  code=0
  timeout 30 "$python_bin" -m genresearch serve --config "experiments/configs/concurrent-$scenario.json" >"$out/$scenario.json" || code=$?
  printf '%s=%s\n' "$scenario" "$code" >>"$out/exit-codes.txt"
  if [[ $code != 2 ]]; then echo "Código inesperado: $scenario=$code" >&2; exit 1; fi
done
"$python_bin" scripts/verify_stage3.py "$out/serve.json" "$out/failure.json" "$out/saturation.json" >"$out/integrity.txt"
cat "$out/tests.txt" "$out/integrity.txt"
