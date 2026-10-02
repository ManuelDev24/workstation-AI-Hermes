"""Punto de entrada único: `aiws <comando>`. Códigos de salida: 0 ok, 1 error, 2 entrada inválida,
3 ruta no autorizada, 4 bot ocupado, 5 timeout."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys

from .core import ROOT, AiwsError, load_config, redact, run_bot

CRED_VARS = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY", "GITHUB_TOKEN"]


def _out(obj) -> None:
    print(redact(json.dumps(obj, indent=2, ensure_ascii=False, default=str)))


def cmd_doctor(_a) -> int:
    def ver(cmd: list[str]) -> str:
        exe = shutil.which(cmd[0])
        if not exe:
            return "NO DISPONIBLE"
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            return (r.stdout or r.stderr).strip().splitlines()[0]
        except Exception as e:  # noqa: BLE001
            return f"error: {type(e).__name__}"

    cfg = load_config()
    checks = {
        "sistema": f"{platform.system()} {platform.mac_ver()[0]} {platform.machine()}",
        "python": sys.version.split()[0],
        "uv": ver(["uv", "--version"]),
        "git": ver(["git", "--version"]),
        "node": ver(["node", "--version"]),
        "hermes": ver(["hermes", "--version"]),
        "claude": ver(["claude", "--version"]),
        "codex": ver(["codex", "--version"]),
    }
    for mod in [
        "pandas",
        "duckdb",
        "openpyxl",
        "matplotlib",
        "httpx",
        "pydantic",
        "pytest",
        "jupyterlab",
    ]:
        try:
            m = __import__(mod)
            checks[f"import {mod}"] = getattr(m, "__version__", "ok")
        except Exception as e:  # noqa: BLE001
            checks[f"import {mod}"] = f"FALLA {e}"
    checks["rutas"] = {
        k: (cfg.resolve(v).exists())
        for k, v in {
            "input": cfg.input_dirs[0],
            "output": cfg.output_dir,
            "sql_db": cfg.sql_database,
        }.items()
    }
    checks["credenciales_en_entorno"] = {
        v: ("disponible" if os.environ.get(v) else "no disponible") for v in CRED_VARS
    }
    checks["canales_externos"] = (
        "habilitados" if cfg.external_channels_enabled else "deshabilitados"
    )
    _out(checks)
    bad = [
        k
        for k, v in checks.items()
        if isinstance(v, str)
        and (v.startswith("FALLA") or v == "NO DISPONIBLE")
        and k not in ("codex",)
    ]
    if bad:
        print("PENDIENTE/FALLO:", ", ".join(bad), file=sys.stderr)
    return 1 if bad else 0


def cmd_init(_a) -> int:
    from .sample_data import build_all

    _out([str(p.relative_to(ROOT)) for p in build_all()])
    return 0


def cmd_analyze(a) -> int:
    from .bots import file_analyst

    r = run_bot("analyst", file_analyst.run, file=a.file, schema_file=a.schema)
    print(f"Informe: {r['informe']}")
    _out(
        [
            {k: h[k] for k in ("hoja", "filas", "duplicados_exactos", "faltantes")}
            for h in r["hojas"]
        ]
    )
    return 0


def cmd_sql(a) -> int:
    from .bots import sql_assistant

    r = run_bot("sql", sql_assistant.run, query=a.query, canned=a.canned, db=a.db)
    print("SQL:", r["sql"])
    print("Columnas:", r["columnas"])
    for row in r["filas"]:
        print("  ", row)
    print("Explicación:", r["explicacion"])
    return 0


def cmd_monitor(a) -> int:
    from .bots import data_monitor

    r = run_bot("monitor", data_monitor.run, watch=a.watch, cooldown_s=a.cooldown)
    _out(r)
    return 0


def cmd_kb(a) -> int:
    from .bots import knowledge

    r = run_bot("kb", knowledge.run, question=a.question, top=a.top)
    if not r["suficiente_evidencia"]:
        print(r["mensaje"])
        return 0
    for h in r["resultados"]:
        print(
            f"- {h['archivo']}:{h['linea']} § {h['seccion']} (puntaje {h['puntaje']})\n    {h['fragmento'][:160]!r}"
        )
    return 0


def cmd_dev(a) -> int:
    from .bots import dev_assistant as d

    if a.action == "prepare":
        _out(run_bot("dev", d.prepare, project=a.project, task=a.task))
    elif a.action == "apply":
        _out(run_bot("dev", d.apply_patch, task=a.task, patch=a.patch))
    elif a.action == "test":
        r = run_bot("dev", d.test, task=a.task)
        print(r["salida"])
        return 0 if r["ok"] else 1
    elif a.action == "summary":
        r = run_bot("dev", d.summary, task=a.task)
        print(
            r["resumen"],
            "\n",
            r["diff"],
            "\nPruebas OK:",
            r["pruebas_ok"],
            "\n",
            r["siguiente_paso"],
        )
    return 0


def cmd_selftest(_a) -> int:
    return subprocess.call([sys.executable, "-m", "pytest", "-q", str(ROOT / "tests")])


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="aiws", description="Bots deterministas de la AI Workstation")
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("doctor", help="diagnóstico del entorno").set_defaults(f=cmd_doctor)
    sp.add_parser("init-sample", help="(re)genera datos sintéticos").set_defaults(f=cmd_init)
    sp.add_parser("selftest", help="ejecuta pytest").set_defaults(f=cmd_selftest)
    s = sp.add_parser("analyze", help="Bot 1: analiza CSV/Excel")
    s.add_argument("file")
    s.add_argument("--schema")
    s.set_defaults(f=cmd_analyze)
    s = sp.add_parser("sql", help="Bot 2: consulta SQL de solo lectura")
    s.add_argument("--query")
    s.add_argument("--canned")
    s.add_argument("--db")
    s.set_defaults(f=cmd_sql)
    s = sp.add_parser("monitor", help="Bot 3: revisa carpeta/ejecuciones")
    s.add_argument("--watch")
    s.add_argument("--cooldown", type=int, default=3600)
    s.set_defaults(f=cmd_monitor)
    s = sp.add_parser("dev", help="Bot 4: sandbox de desarrollo")
    s.add_argument("action", choices=["prepare", "apply", "test", "summary"])
    s.add_argument("--project")
    s.add_argument("--task", required=True)
    s.add_argument("--patch")
    s.set_defaults(f=cmd_dev)
    s = sp.add_parser("kb", help="Bot 5: busca en documentación autorizada")
    s.add_argument("question")
    s.add_argument("--top", type=int, default=3)
    s.set_defaults(f=cmd_kb)
    a = p.parse_args(argv)
    try:
        return a.f(a)
    except AiwsError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return e.exit_code


if __name__ == "__main__":
    sys.exit(main())
