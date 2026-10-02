import pandas as pd

from dataapp.main import DEFAULT, metrics, render


def test_metrics_known_values():
    m = metrics(pd.read_csv(DEFAULT))
    assert (
        m["total"] == 370.0
        and m["mejor_region"] == "Norte"
        and m["por_region"] == {"Norte": 220, "Sur": 150}
    )


def test_render_escapes_html():
    assert "<script>" not in render(
        {"total": 1, "mejor_region": "<script>", "por_region": {"<script>": 1}}
    )
