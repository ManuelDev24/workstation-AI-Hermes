"""Bot 5 — Asistente de conocimiento: búsqueda textual local en carpetas autorizadas (sin embeddings)."""

from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

from ..core import ROOT, InvalidInput

_TOK = re.compile(r"\w+", re.UNICODE)
STOP = {
    "de",
    "la",
    "el",
    "los",
    "las",
    "y",
    "en",
    "un",
    "una",
    "que",
    "se",
    "por",
    "con",
    "para",
    "a",
    "del",
    "es",
    "al",
}
MIN_SCORE = 1.0
EXTS = {".md", ".txt", ".rst"}


def tokens(s: str) -> list[str]:
    return [t for t in (w.lower() for w in _TOK.findall(s)) if t not in STOP and len(t) > 1]


def sections(path: Path):
    title, start, buf = path.stem, 1, []
    for i, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        if line.startswith("#"):
            if buf:
                yield title, start, "\n".join(buf)
            title, start, buf = line.lstrip("# ").strip(), i, []
        else:
            buf.append(line)
    if buf:
        yield title, start, "\n".join(buf)


def run(ctx, question: str, top: int = 3) -> dict:
    if not question or not question.strip():
        raise InvalidInput("La pregunta está vacía.")
    cfg = ctx.cfg
    q = tokens(question)
    if not q:
        raise InvalidInput("La pregunta no contiene términos buscables.")
    docs = []
    for root in cfg.roots(
        cfg.kb_dirs
    ):  # SOLO carpetas autorizadas; sin recorrer el resto del disco
        if not root.exists():
            continue
        for p in sorted(root.rglob("*")):
            if p.is_file() and p.suffix in EXTS and not p.is_symlink():
                for title, line, body in sections(p):
                    docs.append((p, title, line, body))
    n = len(docs) or 1
    df = Counter(t for _, ti, _, b in docs for t in set(tokens(ti + " " + b)))
    scored = []
    for p, title, line, body in docs:
        tf = Counter(tokens(title + " " + title + " " + body))
        s = sum((1 + math.log(tf[t])) * math.log(1 + n / df[t]) for t in q if tf[t])
        if s:
            scored.append((s, p, title, line, body))
    scored.sort(key=lambda x: -x[0])
    hits = [
        {
            "archivo": str(p.relative_to(ROOT)) if ROOT in p.parents else str(p),
            "seccion": t,
            "linea": ln,
            "puntaje": round(s, 2),
            "fragmento": b.strip()[:300],
        }
        for s, p, t, ln, b in scored[:top]
        if s >= MIN_SCORE
    ]
    ctx.logger.info(
        "consulta=%r secciones_indexadas=%d resultados=%d", question[:100], len(docs), len(hits)
    )
    return {
        "pregunta": question,
        "resultados": hits,
        "secciones_indexadas": len(docs),
        "suficiente_evidencia": bool(hits),
        "mensaje": None
        if hits
        else "No encontré evidencia suficiente en la documentación autorizada.",
    }
