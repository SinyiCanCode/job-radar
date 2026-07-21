"""Deduplicação e persistência da fila (JSON + CSV)."""
from __future__ import annotations

import csv
import json

from . import normalize as N
from .models import VagaPontuada


def dedupe(jobs) -> list:
    """Remove repetidas por uid (fonte+id) e por (título, empresa) — pega a
    mesma vaga repostada em fontes diferentes."""
    seen_uid, seen_tc, out = set(), set(), []
    for j in jobs:
        uid = j.uid()
        tc = (N.norm(j.title), N.norm(j.company))
        if uid in seen_uid or (tc[0] and tc in seen_tc):
            continue
        seen_uid.add(uid)
        seen_tc.add(tc)
        out.append(j)
    return out


def _vp_dict(v: VagaPontuada) -> dict:
    j = v.job
    return {
        "score": v.score,
        "title": j.title,
        "company": j.company,
        "modality": j.modality.value,
        "seniority": j.seniority.name.lower(),
        "location": j.location,
        "posted_at": str(j.posted_at) if j.posted_at else None,
        "source": j.source,
        "url": j.url,
        "matched_skills": v.matched_skills,
        "missing_skills": v.missing_skills,
        "flags": v.flags,
        "breakdown": v.breakdown,
    }


def salvar_json(fila, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([_vp_dict(v) for v in fila], f, ensure_ascii=False, indent=2)


def salvar_csv(fila, path: str) -> None:
    campos = ["score", "title", "company", "modality", "seniority", "location",
              "source", "url", "flags", "matched_skills", "missing_skills"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for v in fila:
            d = _vp_dict(v)
            d["flags"] = " | ".join(v.flags)
            d["matched_skills"] = ", ".join(v.matched_skills)
            d["missing_skills"] = ", ".join(v.missing_skills)
            w.writerow({k: d[k] for k in campos})
