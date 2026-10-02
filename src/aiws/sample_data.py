"""Datos sintéticos deterministas (semilla fija) para pruebas y demos."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd

from .core import ROOT

SAMPLE = ROOT / "data" / "sample"


def make_sales_df() -> pd.DataFrame:
    """12 filas con resultados conocidos: 2 duplicados exactos, 2 valores faltantes."""
    rows = [
        (1, "2026-01-05", "Norte", "Laptop", 2, 1000.0),
        (2, "2026-01-06", "Norte", "Mouse", 10, 20.0),
        (3, "2026-01-07", "Sur", "Laptop", 1, 1000.0),
        (4, "2026-01-08", "Sur", "Teclado", 5, 50.0),
        (5, "2026-01-09", "Este", "Mouse", 4, 20.0),
        (6, "2026-01-10", "Este", "Laptop", None, 1000.0),  # falta cantidad
        (7, "2026-01-11", "Oeste", "Teclado", 3, None),  # falta precio
        (8, "2026-01-12", "Oeste", "Mouse", 6, 20.0),
        (9, "2026-01-13", "Norte", "Teclado", 2, 50.0),
        (10, "2026-01-14", "Sur", "Mouse", 8, 20.0),
        (10, "2026-01-14", "Sur", "Mouse", 8, 20.0),  # duplicado exacto
        (10, "2026-01-14", "Sur", "Mouse", 8, 20.0),  # duplicado exacto
    ]
    return pd.DataFrame(rows, columns=["id", "fecha", "region", "producto", "cantidad", "precio"])


def build_all() -> list[Path]:
    SAMPLE.mkdir(parents=True, exist_ok=True)
    out = []
    df = make_sales_df()
    p = SAMPLE / "ventas.csv"
    df.to_csv(p, index=False)
    out.append(p)
    # numérico guardado como texto -> problema de tipos
    bad = df.copy()
    bad["cantidad"] = bad["cantidad"].map(lambda v: "" if pd.isna(v) else str(int(v)))
    bad.loc[1, "cantidad"] = "diez"
    p = SAMPLE / "ventas_tipos.csv"
    bad.to_csv(p, index=False)
    out.append(p)
    # Excel con varias hojas
    p = SAMPLE / "ventas.xlsx"
    with pd.ExcelWriter(p) as xw:
        df.to_excel(xw, sheet_name="ventas", index=False)
        pd.DataFrame(
            {"region": ["Norte", "Sur", "Este", "Oeste"], "meta": [100, 90, 80, 70]}
        ).to_excel(xw, sheet_name="metas", index=False)
    out.append(p)
    # DuckDB: ventas limpias (sin duplicados) para preguntas SQL con resultado conocido
    db = SAMPLE / "sales.duckdb"
    db.unlink(missing_ok=True)
    clean = df.drop_duplicates().dropna()  # noqa: F841 (lo usa DuckDB por replacement scan)
    con = duckdb.connect(str(db))
    con.execute("CREATE TABLE ventas AS SELECT * FROM clean")
    con.close()
    out.append(db)
    # monitor: ejecuciones de ejemplo
    mon = SAMPLE / "monitor"
    (mon / "runs").mkdir(parents=True, exist_ok=True)
    (mon / "ventas_diarias.csv").write_text("id,fecha,monto\n1,2026-01-01,10\n2,2026-01-02,20\n")
    (mon / "runs" / "run1.json").write_text(json.dumps({"job": "etl_ventas", "status": "success"}))
    (mon / "runs" / "run2.json").write_text(
        json.dumps({"job": "etl_inventario", "status": "failed", "error": "timeout"})
    )
    (mon / "expected.yaml").write_text(
        "files:\n  - ventas_diarias.csv\n  - inventario.csv   # ausente a propósito\n"
    )
    out.append(mon)
    # base de conocimiento
    kb = SAMPLE / "kb"
    kb.mkdir(exist_ok=True)
    (kb / "politica_datos.md").write_text(
        "# Política de datos\n\n## Retención\nLos archivos de entrada se conservan 90 días.\n\n"
        "## Acceso\nSolo analistas autorizados pueden leer la carpeta data/input.\n"
    )
    (kb / "guia_sql.md").write_text(
        "# Guía SQL\n\n## Consultas de solo lectura\nLos bots usan conexiones read_only de DuckDB.\n\n"
        "## Límites\nCada consulta devuelve como máximo 1000 filas y expira a los 10 segundos.\n"
    )
    out.append(kb)
    return out
