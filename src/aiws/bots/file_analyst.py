"""Bot 1 — Analista de archivos (CSV/Excel). Solo lectura sobre los originales."""

from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import yaml

from ..core import InvalidInput, authorize, rel

EXTS = {".csv", ".xlsx"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_sheets(path: Path, max_rows: int) -> dict[str, pd.DataFrame]:
    try:
        if path.suffix == ".csv":
            sheets = {"csv": pd.read_csv(path, nrows=max_rows + 1)}
        else:
            sheets = pd.read_excel(path, sheet_name=None, nrows=max_rows + 1)
    except Exception as e:
        raise InvalidInput(f"No se pudo leer {path.name}: {type(e).__name__}: {e}") from e
    for name, df in sheets.items():
        if len(df) > max_rows:
            raise InvalidInput(f"La hoja '{name}' excede el máximo de {max_rows} filas.")
    return sheets


def text_numeric_issues(df: pd.DataFrame) -> dict[str, list[str]]:
    """Columnas de texto donde la mayoría de valores parece numérica pero hay intrusos."""
    out = {}
    for col in df.select_dtypes(include=["object", "string"]):
        s = df[col].dropna().astype(str).str.strip()
        s = s[s != ""]
        if s.empty:
            continue
        num = pd.to_numeric(s, errors="coerce")
        if 0.5 <= num.notna().mean() < 1.0:
            out[col] = sorted(s[num.isna()].unique().tolist())[:5]
    return out


def check_schema(df: pd.DataFrame, schema: dict) -> list[str]:
    probs = []
    for col, kind in schema.items():
        if col not in df.columns:
            probs.append(f"Falta la columna esperada '{col}'.")
            continue
        ok = {
            "int": pd.api.types.is_integer_dtype,
            "float": pd.api.types.is_float_dtype,
            "number": pd.api.types.is_numeric_dtype,
            "str": pd.api.types.is_string_dtype,
        }[kind](df[col])
        if not ok:
            probs.append(f"Columna '{col}': se esperaba {kind}, hay {df[col].dtype}.")
    return probs


def analyze_df(name: str, df: pd.DataFrame, schema: dict | None) -> dict:
    return {
        "hoja": name,
        "filas": len(df),
        "columnas": list(map(str, df.columns)),
        "tipos": {str(c): str(t) for c, t in df.dtypes.items()},
        "faltantes": {str(c): int(v) for c, v in df.isna().sum().items() if v},
        "duplicados_exactos": int(df.duplicated().sum()),
        "texto_numerico": text_numeric_issues(df),
        "esquema": check_schema(df, schema) if schema else None,
        "estadisticas": json.loads(df.describe().round(4).to_json())
        if df.select_dtypes("number").shape[1]
        else {},
    }


def run(ctx, file: str, schema_file: str | None = None) -> dict:
    cfg = ctx.cfg
    path = authorize(file, cfg.roots(cfg.input_dirs))
    if path.suffix.lower() not in EXTS:
        raise InvalidInput(f"Formato no soportado: {path.suffix}. Usa .csv o .xlsx")
    size_mb = path.stat().st_size / 1e6
    if size_mb > cfg.limits.max_file_mb:
        raise InvalidInput(
            f"Archivo de {size_mb:.1f} MB excede el máximo ({cfg.limits.max_file_mb} MB)."
        )
    schema = yaml.safe_load(Path(schema_file).read_text()) if schema_file else None
    before = sha256(path)
    sheets = load_sheets(path, cfg.limits.max_rows)
    out = cfg.resolve(cfg.output_dir) / f"analisis-{path.stem}-{ctx.run_id}"
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for name, df in sheets.items():
        r = analyze_df(name, df, schema if name in ("csv", "ventas") else None)
        num = df.select_dtypes("number")
        charts = []
        if not num.empty:
            num.hist(figsize=(8, 5))
            plt.suptitle(f"Distribuciones — {name}")
            png = out / f"hist-{name}.png"
            plt.savefig(png, dpi=80)
            plt.close("all")
            charts.append(png.name)
        if r["faltantes"]:
            pd.Series(r["faltantes"]).plot.bar(title=f"Valores faltantes — {name}")
            png = out / f"faltantes-{name}.png"
            plt.tight_layout()
            plt.savefig(png, dpi=80)
            plt.close("all")
            charts.append(png.name)
        r["graficos"] = charts
        results.append(r)
    after = sha256(path)
    assert before == after, "el archivo original cambió"  # nunca debería ocurrir
    # código ejecutado + resultados
    (out / "codigo_ejecutado.py").write_text(
        inspect.getsource(__import__(__name__, fromlist=["x"]))
    )
    (out / "resultados.json").write_text(
        json.dumps(
            {"archivo": str(path), "sha256": before, "hojas": results}, indent=2, ensure_ascii=False
        )
    )
    report = out / "informe.md"
    report.write_text(render_report(path, before, results), encoding="utf-8")
    rep_copy = cfg.resolve(cfg.report_dir) / f"{path.stem}-{ctx.run_id}.md"
    rep_copy.write_text(report.read_text(encoding="utf-8"), encoding="utf-8")
    ctx.logger.info("informe=%s", rel(report))
    return {"salida": str(out), "informe": str(report), "hojas": results, "sha256": before}


def render_report(path: Path, digest: str, results: list[dict]) -> str:
    L = [
        f"# Informe de análisis — {path.name}",
        "",
        f"SHA-256 del original (no modificado): `{digest[:16]}…`",
        "",
    ]
    L += ["## Hechos calculados", ""]
    for r in results:
        L += [
            f"### Hoja `{r['hoja']}`",
            f"- Filas: **{r['filas']}**, columnas: **{len(r['columnas'])}** ({', '.join(r['columnas'])})",
        ]
        L.append(f"- Filas duplicadas exactas: **{r['duplicados_exactos']}**")
        if r["faltantes"]:
            L.append(
                "- Valores faltantes: " + ", ".join(f"`{c}`={n}" for c, n in r["faltantes"].items())
            )
        else:
            L.append("- Valores faltantes: ninguno")
        for c, bad in r["texto_numerico"].items():
            L.append(
                f"- Problema de tipos en `{c}`: texto no numérico en columna mayormente numérica: {bad}"
            )
        if r["esquema"] is not None:
            L.append("- Esquema: " + ("cumple" if not r["esquema"] else "; ".join(r["esquema"])))
        for c, s in r["estadisticas"].items():
            L.append(
                f"- `{c}`: media={s['mean']}, mín={s['min']}, máx={s['max']}, n={int(s['count'])}"
            )
        for g in r["graficos"]:
            L.append(f"- Gráfico: `{g}`")
        L.append("")
    L += ["## Interpretación (hipótesis, no verificada)", ""]
    for r in results:
        if r["duplicados_exactos"]:
            L.append(
                f"- En `{r['hoja']}` los duplicados podrían ser cargas repetidas; confirmar con el dueño de los datos antes de eliminarlos."
            )
        if r["faltantes"]:
            L.append(
                f"- Los faltantes en `{r['hoja']}` pueden sesgar promedios; decidir si imputar o excluir."
            )
        if r["texto_numerico"]:
            L.append(
                f"- Hay valores de texto mezclados en columnas numéricas de `{r['hoja']}`; revisar la captura."
            )
    if L[-1] == "":
        L.append("- Sin hallazgos de calidad que interpretar.")
    return "\n".join(L) + "\n"
