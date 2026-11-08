"""Worker observado externamente; carga separada da matriz de desempenho."""
import json
import os
import resource
import sys
import time
from pathlib import Path

from genresearch.server import serve

config = json.loads(Path(sys.argv[1]).read_text())
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 ** 2, 512 * 1024 ** 2))
resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
Path(sys.argv[2]).write_text(str(os.getpid()))
time.sleep(.2)  # Janela declarada para o observador localizar o processo.
result = serve(config)
print(json.dumps(result, sort_keys=True))
raise SystemExit(2 if result["status"] != "completed" else 0)
