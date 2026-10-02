"""Núcleo común: configuración, rutas autorizadas, bloqueo, logs con rotación, métricas, ejecución."""

from __future__ import annotations

import fcntl
import json
import logging
import os
import re
import signal
import time
import uuid
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "configs" / "aiws.yaml"


def logs_base() -> Path:
    """Directorio de logs; AIWS_LOG_DIR permite aislarlo (las pruebas lo usan)."""
    return Path(os.environ.get("AIWS_LOG_DIR") or ROOT / "logs")


class AiwsError(Exception):
    """Error esperado, con mensaje comprensible para el usuario."""

    exit_code = 1


class UnauthorizedPath(AiwsError):
    exit_code = 3


class InvalidInput(AiwsError):
    exit_code = 2


class BusyError(AiwsError):
    exit_code = 4


class BotTimeout(AiwsError):
    exit_code = 5


class Limits(BaseModel):
    max_file_mb: int = 20
    max_rows: int = 1_000_000
    sql_max_rows: int = 1000
    sql_timeout_s: int = 10
    run_timeout_s: int = 120
    retries: int = 1  # reintentos solo para errores de E/S transitorios
    log_max_bytes: int = 1_000_000
    log_backups: int = 5
    keep_run_logs: int = 50


class Config(BaseModel):
    input_dirs: list[str] = ["data/input", "data/sample"]
    output_dir: str = "data/output"
    report_dir: str = "reports"
    kb_dirs: list[str] = ["docs", "data/sample/kb"]
    dev_projects_dir: str = "projects"
    sql_database: str = "data/sample/sales.duckdb"
    monitor_watch_dir: str = "data/sample/monitor"
    external_channels_enabled: bool = False
    limits: Limits = Field(default_factory=Limits)

    def resolve(self, rel: str) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else ROOT / p

    def roots(self, names: list[str]) -> list[Path]:
        return [self.resolve(n).resolve() for n in names]


def load_config(path: Path | None = None) -> Config:
    p = path or CONFIG_PATH
    data = yaml.safe_load(p.read_text()) if p.exists() else {}
    return Config(**(data or {}))


def rel(p: Path) -> str:
    p = Path(p)
    return str(p.relative_to(ROOT)) if ROOT in p.parents else str(p)


def authorize(path: str | Path, roots: list[Path], *, must_exist: bool = True) -> Path:
    """Resuelve symlinks y exige que la ruta quede dentro de alguna raíz autorizada."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    real = p.resolve()
    for r in roots:
        if real == r or r in real.parents:
            if must_exist and not real.exists():
                raise InvalidInput(f"No existe el archivo: {path}")
            return real
    allowed = ", ".join(str(r.relative_to(ROOT)) if ROOT in r.parents else str(r) for r in roots)
    raise UnauthorizedPath(f"Ruta no autorizada: {path}. Rutas permitidas: {allowed}")


# ---------- secretos ----------
_SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_\-]{12,}|gh[pousr]_[A-Za-z0-9]{20,}|xox[abp]-[A-Za-z0-9\-]{10,}"
    r"|(?i:(?:api[_-]?key|token|secret|password)\s*[=:]\s*)\S+)"
)


def redact(text: str) -> str:
    return _SECRET_RE.sub("[REDACTED]", text)


class _RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(str(record.getMessage()))
        record.args = ()
        return True


# ---------- ejecución ----------
class RunContext:
    def __init__(self, bot: str, cfg: Config):
        self.bot = bot
        self.cfg = cfg
        self.run_id = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
        self.log_dir = logs_base() / bot
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(f"aiws.{bot}.{self.run_id}")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        fmt = logging.Formatter("%(asctime)s %(levelname)s [" + self.run_id + "] %(message)s")
        lim = cfg.limits
        self.run_log = self.log_dir / f"run-{self.run_id}.log"
        for h in (
            logging.FileHandler(self.run_log),
            RotatingFileHandler(
                self.log_dir / "bot.log", maxBytes=lim.log_max_bytes, backupCount=lim.log_backups
            ),
        ):
            h.setFormatter(fmt)
            h.addFilter(_RedactFilter())
            self.logger.addHandler(h)
        self._prune(lim.keep_run_logs)

    def _prune(self, keep: int) -> None:
        runs = sorted(self.log_dir.glob("run-*.log"))
        for old in runs[:-keep]:
            old.unlink(missing_ok=True)

    def close(self) -> None:
        for h in list(self.logger.handlers):
            h.close()
            self.logger.removeHandler(h)


@contextmanager
def bot_lock(bot: str):
    """Impide dos ejecuciones simultáneas del mismo bot (flock no bloqueante)."""
    lock_dir = ROOT / "state" / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    fh = open(lock_dir / f"{bot}.lock", "w")  # noqa: SIM115
    try:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise BusyError(f"El bot '{bot}' ya está en ejecución.") from None
        yield
    finally:
        fh.close()


@contextmanager
def time_limit(seconds: int):
    def _handler(signum, frame):
        raise BotTimeout(f"Tiempo máximo excedido ({seconds}s).")

    old = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def _metric(entry: dict) -> None:
    mfile = logs_base() / "metrics.jsonl"
    mfile.parent.mkdir(parents=True, exist_ok=True)
    h = RotatingFileHandler(mfile, maxBytes=1_000_000, backupCount=3)
    h.emit(logging.LogRecord("m", logging.INFO, "", 0, json.dumps(entry), None, None))
    h.close()


def run_bot(bot: str, fn, cfg: Config | None = None, **kwargs):
    """Ejecuta fn(ctx, **kwargs) con bloqueo, timeout, reintentos limitados, log y métricas."""
    cfg = cfg or load_config()
    ctx = RunContext(bot, cfg)
    t0 = time.time()
    status, error = "ok", None
    try:
        with bot_lock(bot):
            attempts = cfg.limits.retries + 1
            for i in range(attempts):
                try:
                    ctx.logger.info("inicio bot=%s intento=%d args=%s", bot, i + 1, kwargs)
                    with time_limit(cfg.limits.run_timeout_s):
                        return fn(ctx, **kwargs)
                except (OSError, TimeoutError) as e:  # transitorios: reintento limitado
                    ctx.logger.warning("error transitorio: %s", e)
                    if i + 1 == attempts:
                        raise AiwsError(f"Fallo de E/S tras {attempts} intentos: {e}") from e
                    time.sleep(0.5)
    except AiwsError as e:
        status, error = "error", f"{type(e).__name__}: {e}"
        ctx.logger.error("%s", error)
        raise
    except Exception as e:  # bug inesperado: se registra y se informa
        status, error = "crash", f"{type(e).__name__}: {e}"
        ctx.logger.exception("fallo inesperado")
        raise
    finally:
        dur = round(time.time() - t0, 3)
        _metric(
            {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "bot": bot,
                "run_id": ctx.run_id,
                "status": status,
                "duration_s": dur,
                "error": redact(error) if error else None,
                "tokens": None,  # los bots deterministas no consumen modelo
            }
        )
        ctx.logger.info("fin status=%s dur=%ss", status, dur)
        ctx.close()
