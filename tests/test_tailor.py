"""Testes do CV Tailor (Fase 2)."""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.models import Job                       # noqa: E402
from src.tailor import gerar_dossie              # noqa: E402

CAND = {
    "skills": ["python", "sql", "postgresql", "etl", "docker"],
    "resumo_base": "base",
    "projetos": [
        {"nome": "A", "tech": ["python", "etl", "docker"]},
        {"nome": "B", "tech": ["python", "react"]},
    ],
}


def _job(desc, title="Vaga X"):
    return Job(source="t", external_id="1", title=title, company="C", url="u", description=desc)


def test_cobertura_espelhar_e_gaps():
    d = gerar_dossie(_job("Requisitos: Python, SQL, Airflow e AWS."), CAND)
    assert "python" in d.espelhar and "sql" in d.espelhar
    assert "airflow" in d.gaps and "aws" in d.gaps
    assert 0 < d.cobertura < 100


def test_projeto_destaque_mais_aderente():
    d = gerar_dossie(_job("Pipeline de ETL com Python e Docker."), CAND)
    assert d.projeto_destaque == "A"


def test_vaga_sem_tech_zera():
    d = gerar_dossie(_job("Vaga de vendas e atendimento ao cliente."), CAND)
    assert d.cobertura == 0.0
    assert d.espelhar == []


if __name__ == "__main__":
    fns = [g for n, g in sorted(globals().items()) if n.startswith("test_") and callable(g)]
    for fn in fns:
        fn(); print("PASS", fn.__name__)
    print(f"{len(fns)} ok")
