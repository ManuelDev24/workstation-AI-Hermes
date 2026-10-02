"""Cuenta líneas/palabras de un archivo de texto. Códigos de salida: 0 ok, 2 entrada inválida, 1 error."""

import argparse
import sys
from pathlib import Path

MAX_BYTES = 5_000_000


def count(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"no existe el archivo: {path}")
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("archivo demasiado grande (máx 5 MB)")
    text = path.read_text(errors="replace")
    return {"lineas": len(text.splitlines()), "palabras": len(text.split())}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mycli", description="Cuenta líneas y palabras.")
    p.add_argument("archivo", type=Path, help="archivo de texto a analizar")
    p.add_argument("--solo", choices=["lineas", "palabras"], help="mostrar solo una métrica")
    a = p.parse_args(argv)
    try:
        r = count(a.archivo)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(r[a.solo] if a.solo else r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
