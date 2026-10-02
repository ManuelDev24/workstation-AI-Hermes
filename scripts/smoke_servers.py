"""Arranca cada servidor de plantilla en localhost, comprueba respuesta y que no queden procesos residuales."""

import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

T = Path(__file__).resolve().parents[1] / "projects" / "templates"
ENV = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")}
CASES = [
    ("api-python", ["uv", "run", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8765"], 8765, "/health", "ok"),
    ("data-app", ["uv", "run", "dataapp", "--serve", "--port", "8766"], 8766, "/", "Ingresos"),
    ("web-react", ["pnpm", "exec", "vite", "--host", "127.0.0.1", "--port", "8767", "--strictPort"], 8767, "/", "root"),
]


def port_open(p: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", p)) == 0


def main() -> int:
    only = sys.argv[1:] 
    rc = 0
    for name, cmd, port, path, expect in CASES:
        if only and name not in only:
            continue
        proc = subprocess.Popen(cmd, cwd=T / name, env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        ok = False
        for _ in range(60):
            if port_open(port):
                try:
                    body = urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=3).read().decode()
                    ok = expect in body
                except Exception:  # noqa: BLE001
                    pass
                break
            time.sleep(0.5)
        os.killpg(proc.pid, signal.SIGINT)
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
        time.sleep(1)
        residual = port_open(port)
        print(f"{name}: responde={ok} puerto_libre_tras_detener={not residual}")
        rc |= int(not ok or residual)
    return rc


if __name__ == "__main__":
    sys.exit(main())
