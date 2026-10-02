import pytest


@pytest.fixture(autouse=True)
def _isolated_logs(tmp_path, monkeypatch):
    monkeypatch.setenv("AIWS_LOG_DIR", str(tmp_path / "logs"))
