"""Lee datos sintéticos, calcula métricas y los sirve en una página HTML local (solo 127.0.0.1)."""

import argparse
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pandas as pd

DEFAULT = Path(__file__).resolve().parents[2] / "data" / "sample.csv"


def metrics(df: pd.DataFrame) -> dict:
    por_region = df.groupby("region")["ingreso"].sum()
    return {
        "total": float(df["ingreso"].sum()),
        "mejor_region": str(por_region.idxmax()),
        "por_region": por_region.to_dict(),
    }


def render(m: dict) -> str:
    rows = "".join(
        f"<tr><td>{html.escape(k)}</td><td>{v:g}</td></tr>" for k, v in m["por_region"].items()
    )
    return (
        f"<html><body><h1>Ingresos</h1><p>Total: {m['total']:g} — mejor región: "
        f"{html.escape(m['mejor_region'])}</p><table>{rows}</table></body></html>"
    )


class Handler(BaseHTTPRequestHandler):
    page = ""

    def do_GET(self):  # noqa: N802
        body = self.page.encode()
        self.send_response(200 if self.path == "/" else 404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body if self.path == "/" else b"no encontrado")

    def log_message(self, *a):
        pass


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="dataapp")
    p.add_argument("--csv", type=Path, default=DEFAULT)
    p.add_argument("--serve", action="store_true", help="servir en http://127.0.0.1:PORT")
    p.add_argument("--port", type=int, default=8501)
    a = p.parse_args(argv)
    m = metrics(pd.read_csv(a.csv))
    if not a.serve:
        print(m)
        return 0
    Handler.page = render(m)
    srv = HTTPServer(("127.0.0.1", a.port), Handler)  # nunca 0.0.0.0
    print(f"http://127.0.0.1:{a.port}  (Ctrl+C para detener)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
