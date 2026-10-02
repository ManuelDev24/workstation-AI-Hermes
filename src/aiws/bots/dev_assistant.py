"""Bot 4 — Asistente de desarrollo. Trabaja en una COPIA aislada con repo git propio (state/dev/<tarea>).

Nunca toca el proyecto original, no hace commit/push/merge en él, y no usa comandos destructivos.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from ..core import ROOT, AiwsError, InvalidInput, authorize

DEV = ROOT / "state" / "dev"
GIT_ENV = [
    "-c",
    "user.name=aiws-sandbox",
    "-c",
    "user.email=sandbox@localhost",
    "-c",
    "commit.gpgsign=false",
]
IGNORE = shutil.ignore_patterns(
    ".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", "dist"
)


def _git(cwd: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", *GIT_ENV, *args], cwd=cwd, capture_output=True, text=True, timeout=60
    )
    if r.returncode:
        raise AiwsError(f"git {' '.join(args)} falló: {r.stderr.strip()[:300]}")
    return r.stdout


def sandbox(task: str) -> Path:
    if not task.replace("-", "").replace("_", "").isalnum():
        raise InvalidInput("Nombre de tarea inválido (usa letras, números, - y _).")
    return DEV / task


def prepare(ctx, project: str, task: str) -> dict:
    cfg = ctx.cfg
    src = authorize(
        ROOT / cfg.dev_projects_dir / project if not Path(project).is_absolute() else project,
        cfg.roots([cfg.dev_projects_dir]),
    )
    sb = sandbox(task)
    if sb.exists():
        raise InvalidInput(
            f"La tarea '{task}' ya existe en {sb}. Usa otro nombre o bórrala tú manualmente."
        )
    shutil.copytree(src, sb, ignore=IGNORE)
    _git(sb, "init", "-q", "-b", "baseline")
    (sb / ".git" / "info" / "exclude").write_text("__pycache__/\n*.pyc\n.pytest_cache/\n")
    _git(sb, "add", "-A")
    _git(sb, "commit", "-q", "-m", "baseline")
    _git(sb, "checkout", "-q", "-b", f"task/{task}")
    ctx.logger.info("sandbox=%s origen=%s", sb, src)
    return {"sandbox": str(sb), "rama": f"task/{task}", "origen_intacto": str(src)}


def apply_patch(ctx, task: str, patch: str) -> dict:
    sb = sandbox(task)
    if not sb.exists():
        raise InvalidInput(f"No existe la tarea '{task}'. Ejecuta 'aiws dev prepare' primero.")
    pp = Path(patch).resolve()
    if not pp.exists():
        raise InvalidInput(f"No existe el parche: {patch}")
    _git(sb, "apply", "--check", str(pp))
    _git(sb, "apply", str(pp))
    return {"aplicado": str(pp)}


def test(ctx, task: str) -> dict:
    sb = sandbox(task)
    if not sb.exists():
        raise InvalidInput(f"No existe la tarea '{task}'.")
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        cwd=sb,
        capture_output=True,
        text=True,
        timeout=ctx.cfg.limits.run_timeout_s,
        env={k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")}
        | {"PYTHONDONTWRITEBYTECODE": "1"},
    )
    ctx.logger.info("pytest rc=%d", r.returncode)
    return {"ok": r.returncode == 0, "salida": (r.stdout + r.stderr)[-1500:]}


def summary(ctx, task: str) -> dict:
    sb = sandbox(task)
    if not sb.exists():
        raise InvalidInput(f"No existe la tarea '{task}'.")
    _git(sb, "add", "-A", "-N")
    diff = _git(sb, "diff", "baseline")
    stat = _git(sb, "diff", "--stat", "baseline")
    t = test(ctx, task)
    return {
        "diff": diff,
        "resumen": stat.strip(),
        "pruebas_ok": t["ok"],
        "siguiente_paso": f"Revisa el diff; para integrarlo copia los cambios tú mismo desde {sb}. "
        "El bot no hace commit/push/merge/despliegue.",
    }
