import hashlib
import shutil
from pathlib import Path

import pytest

from aiws import sample_data
from aiws.bots import data_monitor, dev_assistant, file_analyst, knowledge, sql_assistant
from aiws.core import (
    ROOT,
    BusyError,
    InvalidInput,
    UnauthorizedPath,
    bot_lock,
    load_config,
    logs_base,
    redact,
    run_bot,
)

SAMPLE = ROOT / "data" / "sample"


@pytest.fixture(scope="session", autouse=True)
def _samples():
    sample_data.build_all()


@pytest.fixture
def cfg(tmp_path):
    c = load_config()
    c.output_dir = str(tmp_path / "out")
    c.report_dir = str(tmp_path / "rep")
    (tmp_path / "rep").mkdir()
    return c


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---- Bot 1
def test_csv_stats_match_expected_and_original_untouched(cfg):
    src = SAMPLE / "ventas.csv"
    before = sha(src)
    r = run_bot("analyst", file_analyst.run, cfg=cfg, file=str(src))
    h = r["hojas"][0]
    assert h["filas"] == 12
    assert h["duplicados_exactos"] == 2
    assert h["faltantes"] == {"cantidad": 1, "precio": 1}
    assert sha(src) == before
    rep = Path(r["informe"]).read_text()
    assert "Hechos calculados" in rep and "Interpretación" in rep
    assert (Path(r["salida"]) / "codigo_ejecutado.py").exists()


def test_excel_multisheet(cfg):
    r = run_bot("analyst", file_analyst.run, cfg=cfg, file=str(SAMPLE / "ventas.xlsx"))
    assert {h["hoja"] for h in r["hojas"]} == {"ventas", "metas"}


def test_text_in_numeric_column_detected(cfg):
    r = run_bot("analyst", file_analyst.run, cfg=cfg, file=str(SAMPLE / "ventas_tipos.csv"))
    assert "cantidad" in r["hojas"][0]["texto_numerico"]


def test_schema_violation(cfg, tmp_path):
    sch = tmp_path / "s.yaml"
    sch.write_text("cantidad: int\nnoexiste: str\n")
    r = run_bot(
        "analyst", file_analyst.run, cfg=cfg, file=str(SAMPLE / "ventas.csv"), schema_file=str(sch)
    )
    assert any("noexiste" in p for p in r["hojas"][0]["esquema"])


def test_invalid_extension_and_missing(cfg, tmp_path):
    bad = SAMPLE / "x.txt"
    bad.write_text("hola")
    try:
        with pytest.raises(InvalidInput):
            run_bot("analyst", file_analyst.run, cfg=cfg, file=str(bad))
    finally:
        bad.unlink()
    with pytest.raises(InvalidInput):
        run_bot("analyst", file_analyst.run, cfg=cfg, file=str(SAMPLE / "nope.csv"))


def test_unauthorized_path_blocked(cfg):
    with pytest.raises(UnauthorizedPath):
        run_bot("analyst", file_analyst.run, cfg=cfg, file="/etc/hosts")
    with pytest.raises(UnauthorizedPath):
        run_bot(
            "analyst", file_analyst.run, cfg=cfg, file=str(SAMPLE / ".." / ".." / "pyproject.toml")
        )


def test_symlink_escape_blocked(cfg, tmp_path):
    link = SAMPLE / "escape.csv"
    link.symlink_to(ROOT / "pyproject.toml")
    try:
        with pytest.raises(UnauthorizedPath):
            run_bot("analyst", file_analyst.run, cfg=cfg, file=str(link))
    finally:
        link.unlink()


def test_size_limit(cfg):
    cfg.limits.max_file_mb = 0
    with pytest.raises(InvalidInput):
        run_bot("analyst", file_analyst.run, cfg=cfg, file=str(SAMPLE / "ventas.csv"))


# ---- Bot 2
def test_sql_known_result(cfg):
    r = run_bot("sql", sql_assistant.run, cfg=cfg, canned="total_por_region")
    got = {row[0]: row[1] for row in r["filas"]}
    # ventas limpias: Norte=2*1000+10*20+2*50=2300 ; Sur=1000+250+160=1410 ; Este=80 ; Oeste=120
    assert got == {"Este": 80.0, "Norte": 2300.0, "Oeste": 120.0, "Sur": 1410.0}
    assert r["sql"] and r["explicacion"]


@pytest.mark.parametrize(
    "q",
    [
        "DROP TABLE ventas",
        "DELETE FROM ventas",
        "INSERT INTO ventas VALUES (1)",
        "SELECT 1; DROP TABLE ventas",
        "CREATE TABLE x AS SELECT 1",
    ],
)
def test_sql_writes_rejected(cfg, q):
    with pytest.raises(InvalidInput):
        run_bot("sql", sql_assistant.run, cfg=cfg, query=q)


def test_sql_engine_blocks_write_even_if_prefilter_bypassed(cfg):
    # WITH ... INSERT pasa el prefiltro léxico pero el motor read_only debe rechazarlo
    before = sha(SAMPLE / "sales.duckdb")
    with pytest.raises(InvalidInput):
        run_bot(
            "sql",
            sql_assistant.run,
            cfg=cfg,
            query="WITH a AS (SELECT 1) INSERT INTO ventas SELECT * FROM ventas",
        )
    assert sha(SAMPLE / "sales.duckdb") == before


def test_sql_no_external_file_access(cfg):
    with pytest.raises(InvalidInput):
        run_bot("sql", sql_assistant.run, cfg=cfg, query="SELECT * FROM read_csv('/etc/hosts')")


def test_sql_row_limit_and_timeout(cfg):
    cfg.limits.sql_max_rows = 5
    r = run_bot("sql", sql_assistant.run, cfg=cfg, query="SELECT * FROM range(100)")
    assert len(r["filas"]) == 5 and r["truncado"]
    cfg.limits.sql_timeout_s = 1
    with pytest.raises(Exception, match="tiempo máximo"):
        run_bot(
            "sql", sql_assistant.run, cfg=cfg, query="SELECT COUNT(*) FROM range(100000000000) a"
        )


# ---- Bot 3
def test_monitor_missing_file_schema_change_failure_and_dedupe(cfg, tmp_path, monkeypatch):
    monkeypatch.setattr(data_monitor, "STATE", tmp_path / "state")
    watch = tmp_path / "watch"
    shutil.copytree(SAMPLE / "monitor", watch)
    cfg.input_dirs = [str(tmp_path)]
    r1 = run_bot("monitor", data_monitor.run, cfg=cfg, watch=str(watch))
    tipos = {a["tipo"] for a in r1["alertas_nuevas"]}
    assert tipos == {"archivo_faltante", "ejecucion_fallida"}
    r2 = run_bot("monitor", data_monitor.run, cfg=cfg, watch=str(watch))
    assert r2["alertas_nuevas"] == [] and r2["suprimidas"] == 2  # sin duplicados
    (watch / "ventas_diarias.csv").write_text("id,fecha,importe\n1,2026-01-01,10\n")
    r3 = run_bot("monitor", data_monitor.run, cfg=cfg, watch=str(watch))
    assert [a["tipo"] for a in r3["alertas_nuevas"]] == ["cambio_esquema"]
    assert r3["canales_externos"] == "deshabilitados"


# ---- Bot 4
def test_dev_flow_isolated_and_original_untouched(cfg, tmp_path, monkeypatch):
    monkeypatch.setattr(dev_assistant, "DEV", tmp_path / "dev")
    orig = ROOT / "projects" / "sample-repo"
    snap = {p: sha(p) for p in orig.rglob("*.py")}
    run_bot("dev", dev_assistant.prepare, cfg=cfg, project="sample-repo", task="t1")
    assert dev_assistant.test(
        type("C", (), {"cfg": cfg, "logger": __import__("logging").getLogger("x")})(), "t1"
    )["ok"]
    run_bot(
        "dev",
        dev_assistant.apply_patch,
        cfg=cfg,
        task="t1",
        patch=str(ROOT / "bots/dev-assistant/tasks/empty-average.patch"),
    )
    s = run_bot("dev", dev_assistant.summary, cfg=cfg, task="t1")
    assert s["pruebas_ok"] and "calc/__init__.py" in s["diff"] and "test_average_empty" in s["diff"]
    assert ".pyc" not in s["diff"] and "__pycache__" not in s["diff"]
    assert snap == {p: sha(p) for p in orig.rglob("*.py")}
    assert not (orig / ".git").exists()


def test_dev_rejects_outside_project(cfg):
    with pytest.raises(UnauthorizedPath):
        run_bot("dev", dev_assistant.prepare, cfg=cfg, project="/etc", task="evil")
    with pytest.raises(InvalidInput):
        run_bot("dev", dev_assistant.prepare, cfg=cfg, project="sample-repo", task="../x")


# ---- Bot 5
def test_kb_finds_reference_and_admits_no_evidence(cfg):
    r = run_bot(
        "kb", knowledge.run, cfg=cfg, question="¿Cuántos días se conservan los archivos de entrada?"
    )
    assert r["resultados"][0]["archivo"].endswith("politica_datos.md")
    assert r["resultados"][0]["seccion"] == "Retención" and r["resultados"][0]["linea"] == 3
    r = run_bot("kb", knowledge.run, cfg=cfg, question="receta de arepas venezolanas")
    assert not r["suficiente_evidencia"] and "evidencia" in r["mensaje"]


def test_kb_empty_question(cfg):
    with pytest.raises(InvalidInput):
        run_bot("kb", knowledge.run, cfg=cfg, question="  ")


# ---- Operación
def test_lock_prevents_concurrent_runs():
    with bot_lock("locktest"), pytest.raises(BusyError), bot_lock("locktest"):
        pass


def test_redaction_and_no_secrets_in_logs(cfg):
    assert "sk-" not in redact("clave sk-abcdefghijklmnop1234")
    assert "hunter2" not in redact("password=hunter2")
    with pytest.raises(InvalidInput):
        run_bot(
            "sql",
            sql_assistant.run,
            cfg=cfg,
            query="SELECT 'api_key=sk-SECRET1234567890abcd'; DROP x",
        )
    logs = (logs_base() / "sql" / "bot.log").read_text()
    assert "SECRET1234567890" not in logs


def test_missing_credentials_reported(monkeypatch):
    from aiws.cli import main

    for v in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(v, raising=False)
    assert main(["kb", "retención"]) == 0  # los bots deterministas no necesitan credenciales


def test_cli_exit_codes():
    from aiws.cli import main

    assert main(["analyze", "/etc/hosts"]) == 3
    assert main(["sql", "--query", "DROP TABLE x"]) == 2
