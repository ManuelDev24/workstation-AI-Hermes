"""Bot 2 — Asistente SQL. Escrituras impedidas por conexión DuckDB read_only + acceso externo desactivado."""

from __future__ import annotations

import re
import threading

import duckdb

from ..core import AiwsError, InvalidInput, authorize, rel

CANNED = {
    "total_por_region": (
        "Ingreso total por región",
        "SELECT region, SUM(cantidad*precio) AS ingreso FROM ventas GROUP BY region ORDER BY region",
    ),
    "top_producto": (
        "Producto con más unidades vendidas",
        "SELECT producto, SUM(cantidad) AS unidades FROM ventas GROUP BY producto ORDER BY unidades DESC LIMIT 1",
    ),
    "total_filas": ("Número de ventas", "SELECT COUNT(*) AS n FROM ventas"),
}
_FIRST = re.compile(r"^\s*(select|with|describe|show|pragma\s+table_info)\b", re.IGNORECASE)


def run(ctx, query: str | None = None, canned: str | None = None, db: str | None = None) -> dict:
    cfg = ctx.cfg
    if canned:
        if canned not in CANNED:
            raise InvalidInput(f"Pregunta desconocida '{canned}'. Opciones: {', '.join(CANNED)}")
        title, query = CANNED[canned]
    else:
        title = "Consulta libre"
    if not query or not query.strip():
        raise InvalidInput("Falta la consulta SQL (--query) o una pregunta predefinida (--canned).")
    stripped = query.strip().rstrip(";")
    if ";" in stripped:
        raise InvalidInput("Solo se permite una sentencia por consulta.")
    if not _FIRST.match(stripped):
        raise InvalidInput("Solo se permiten consultas de lectura (SELECT/WITH/DESCRIBE/SHOW).")
    dbp = authorize(db or cfg.sql_database, cfg.roots(cfg.input_dirs))
    con = duckdb.connect(str(dbp), read_only=True)  # control técnico: el motor rechaza escrituras
    try:
        con.execute("SET enable_external_access=false")  # sin lectura de archivos/red desde SQL
        con.execute("SET lock_configuration=true")
        n = cfg.limits.sql_max_rows
        timer = threading.Timer(cfg.limits.sql_timeout_s, con.interrupt)
        timer.start()
        try:
            if stripped.lower().startswith(("describe", "show", "pragma")):
                cur = con.execute(stripped)
            else:
                cur = con.execute(f"SELECT * FROM ({stripped}) LIMIT {n + 1}")
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
        except duckdb.InterruptException:
            raise AiwsError(
                f"La consulta superó el tiempo máximo ({cfg.limits.sql_timeout_s}s)."
            ) from None
        except duckdb.Error as e:
            raise InvalidInput(f"El motor SQL rechazó la consulta: {e}") from e
        finally:
            timer.cancel()
    finally:
        con.close()
    truncated = len(rows) > n
    rows = rows[:n]
    ctx.logger.info("sql=%s filas=%d truncado=%s", stripped[:200], len(rows), truncated)
    return {
        "titulo": title,
        "sql": stripped,
        "columnas": cols,
        "filas": [list(r) for r in rows],
        "truncado": truncated,
        "explicacion": f"{title}: la consulta devolvió {len(rows)} fila(s)"
        + (f" (truncado a {n})." if truncated else ".")
        + f" Base: {rel(dbp)}, modo solo lectura.",
    }
