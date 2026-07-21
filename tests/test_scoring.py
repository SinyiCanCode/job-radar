"""Testes do motor de qualificação + pipeline end-to-end.

Roda com:   python -m pytest tests/ -v
Ou direto:  python tests/test_scoring.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.models import Modalidade, Perfil, Senioridade   # noqa: E402
from src.scoring import qualificar                        # noqa: E402
from src.scrapers.base import build_job                   # noqa: E402

PERFIL_YAML = os.path.join(ROOT, "perfil.yaml")
CONFIG_YAML = os.path.join(ROOT, "config.yaml")


def perfil_teste() -> Perfil:
    return Perfil(
        titulos_alvo=["estagio em dados", "analista de dados junior",
                      "engenheiro de dados junior", "desenvolvedor python junior",
                      "analista de dados"],
        skills=["python", "sql", "postgresql", "pandas", "etl", "fastapi",
                "docker", "git", "api rest", "modelagem de dados", "excel"],
        skills_obrigatorias=["python"],
        senioridades_aceitas=[Senioridade.ESTAGIO, Senioridade.TRAINEE, Senioridade.JUNIOR],
        modalidades_aceitas=[Modalidade.REMOTO],
        localizacao="Parnamirim, RN",
        aceita_remoto_global=False,
        salario_minimo=None,
        keywords_bonus=["fintech", "financeiro", "contabil", "juridico", "etl", "dados"],
        keywords_veto=["senior", "especialista", "tech lead", "coordenador", "gerente"],
    )


def test_vaga_ideal_sobrevive_com_score_alto():
    job = build_job("t", "1", "Estágio em Dados", "DataLab", "http://x",
                    "Python, SQL e pandas para ETL. 100% remoto. PostgreSQL e Git.",
                    location="Remoto - Brasil", posted_at="2026-07-11")
    v = qualificar(job, perfil_teste())
    assert not v.eliminada
    assert v.score >= 60
    assert "python" in v.matched_skills


def test_presencial_eliminada():
    job = build_job("t", "5", "Analista de Dados Júnior", "VarejoTech", "http://x",
                    "Atuação presencial em São Paulo. Python e SQL.",
                    location="São Paulo, SP - Presencial")
    v = qualificar(job, perfil_teste())
    assert v.eliminada
    assert "modalidade" in v.motivo_eliminacao


def test_senior_eliminada_por_veto_titulo():
    job = build_job("t", "4", "Analista de Dados Sênior", "BigCorp", "http://x",
                    "Liderança técnica. Python e SQL. Remoto.")
    v = qualificar(job, perfil_teste())
    assert v.eliminada
    assert "veto" in v.motivo_eliminacao or "senioridade" in v.motivo_eliminacao


def test_fora_da_area_eliminada():
    job = build_job("t", "6", "Enfermeiro Plantonista", "Hospital", "http://x",
                    "Atendimento a pacientes. Plantão 12x36. COREN obrigatório.",
                    location="Natal, RN")
    v = qualificar(job, perfil_teste())
    assert v.eliminada
    assert "rea" in v.motivo_eliminacao  # "fora da área"


def test_junior_fake_vira_flag_nao_corte():
    job = build_job("t", "3", "Desenvolvedor Python Júnior", "SoftX", "http://x",
                    "Vaga júnior. Requisito: 3 anos de experiência com Python. Remoto.")
    v = qualificar(job, perfil_teste())
    assert not v.eliminada
    assert any("fake" in f for f in v.flags)


def test_remoto_fora_br_eliminada():
    job = build_job("t", "7", "Junior Data Analyst", "GlobalCorp", "http://x",
                    "Work with Python and SQL. Fully remote.", location="USA Only")
    v = qualificar(job, perfil_teste())
    assert v.eliminada
    assert "fora do BR" in v.motivo_eliminacao


def test_skill_obrigatoria_faltando_penaliza_e_flag():
    job = build_job("t", "8", "Estágio em BI", "AnalyticsCo", "http://x",
                    "Dashboards com Power BI, Excel e SQL. Remoto. Não exige experiência.",
                    location="Remoto - Brasil")
    v = qualificar(job, perfil_teste())
    assert not v.eliminada
    assert v.breakdown["skills"] <= 0.45
    assert any("obrigat" in f for f in v.flags)


def test_ranqueia_por_aderencia():
    p = perfil_teste()
    forte = build_job("t", "a", "Analista de Dados Júnior", "X", "http://a",
                      "Python, SQL, PostgreSQL, pandas, ETL, Docker. Remoto.")
    fraca = build_job("t", "b", "Analista de Dados Júnior", "Y", "http://b",
                      "SQL e Excel para relatórios. Remoto.")
    assert qualificar(forte, p).score > qualificar(fraca, p).score


def test_pipeline_fixture_end_to_end():
    from src.pipeline import rodar
    res = rodar(perfil_path=PERFIL_YAML, config_path=CONFIG_YAML,
                fontes=["fixture"], query="")
    assert res.coletadas == 9
    assert len(res.eliminadas) >= 4          # sênior, presencial, enfermeiro, USA-only
    assert res.fila, "a fila não deveria estar vazia"
    assert res.fila[0].score >= 60           # topo é uma vaga forte de dados
    # a vaga fora da área nunca entra na fila
    assert all("Enfermeiro" not in v.job.title for v in res.fila)


if __name__ == "__main__":
    # runner manual (sem pytest)
    fns = [g for n, g in sorted(globals().items()) if n.startswith("test_") and callable(g)]
    falhas = 0
    for fn in fns:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except AssertionError as e:
            falhas += 1
            print(f"  FAIL  {fn.__name__}: {e}")
        except Exception as e:
            falhas += 1
            print(f"  ERRO  {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - falhas}/{len(fns)} testes passaram")
    sys.exit(1 if falhas else 0)
