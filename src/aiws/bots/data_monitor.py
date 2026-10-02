"""Bot 3 — Monitor de datos: archivos faltantes, cambios de esquema, fallos de ejecuciones. Alertas solo locales."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import pandas as pd
import yaml

from ..core import ROOT, authorize

STATE = ROOT / "state" / "monitor"


def _load(p: Path, default):
    return json.loads(p.read_text()) if p.exists() else default


def run(ctx, watch: str | None = None, cooldown_s: int = 3600) -> dict:
    cfg = ctx.cfg
    wdir = authorize(watch or cfg.monitor_watch_dir, cfg.roots(cfg.input_dirs))
    STATE.mkdir(parents=True, exist_ok=True)
    schemas_p, seen_p = STATE / "schemas.json", STATE / "seen.json"
    schemas, seen = _load(schemas_p, {}), _load(seen_p, {})
    findings: list[dict] = []

    exp = wdir / "expected.yaml"
    expected = (yaml.safe_load(exp.read_text()) or {}).get("files", []) if exp.exists() else []
    for f in expected:
        if not (wdir / f).exists():
            findings.append({"tipo": "archivo_faltante", "clave": f, "detalle": f"Falta {f}"})

    for csv in sorted(wdir.glob("*.csv")):
        cols = list(pd.read_csv(csv, nrows=0).columns)
        if csv.name in schemas and schemas[csv.name] != cols:
            findings.append(
                {
                    "tipo": "cambio_esquema",
                    "clave": csv.name,
                    "detalle": f"{csv.name}: columnas {schemas[csv.name]} -> {cols}",
                }
            )
        schemas[csv.name] = schemas.get(csv.name, cols)

    for rp in sorted((wdir / "runs").glob("*.json")) if (wdir / "runs").exists() else []:
        r = json.loads(rp.read_text())
        if r.get("status") != "success":
            findings.append(
                {
                    "tipo": "ejecucion_fallida",
                    "clave": r.get("job", rp.stem),
                    "detalle": f"Job {r.get('job')} falló: {r.get('error', 'sin detalle')}",
                }
            )

    now = time.time()
    new_alerts, suppressed = [], 0
    active = set()
    for f in findings:
        fp = hashlib.sha1(f"{f['tipo']}|{f['clave']}|{f['detalle']}".encode()).hexdigest()[:12]
        active.add(fp)
        if fp in seen and now - seen[fp] < cooldown_s:
            suppressed += 1
            continue
        seen[fp] = now
        f["id"] = fp
        new_alerts.append(f)
    seen = {
        k: v for k, v in seen.items() if k in active
    }  # al resolverse, la alerta puede volver a dispararse

    with open(ctx.log_dir / "events.jsonl", "a") as ev:
        ev.writelines(
            json.dumps({"ts": time.strftime("%FT%T"), **a}, ensure_ascii=False) + "\n"
            for a in new_alerts
        )
    with open(STATE / "alerts.jsonl", "a") as al:  # canal local; no hay canales externos
        al.writelines(
            json.dumps({"ts": time.strftime("%FT%T"), **a}, ensure_ascii=False) + "\n"
            for a in new_alerts
        )
    schemas_p.write_text(json.dumps(schemas, indent=1))
    seen_p.write_text(json.dumps(seen))
    ctx.logger.info(
        "hallazgos=%d nuevas=%d suprimidas=%d", len(findings), len(new_alerts), suppressed
    )
    return {
        "hallazgos": len(findings),
        "alertas_nuevas": new_alerts,
        "suprimidas": suppressed,
        "canales_externos": "deshabilitados",
    }
