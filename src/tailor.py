"""CV Tailor — adapta o CV a cada vaga (Fase 2 do roadmap).

Heuristico e offline: cruza os requisitos do anuncio com o inventario do
candidato (cv_base.yaml) e devolve um dossie por vaga:
  - cobertura: quanto teu perfil cobre os requisitos
  - espelhar: keywords do anuncio que voce TEM (use as palavras exatas no CV)
  - gaps: requisitos que faltam (aprender ou omitir)
  - projeto_destaque: qual projeto seu puxar pra esta vaga
  - resumo_adaptado: um resumo na linguagem da vaga
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import normalize as N

# Vocabulario tecnico amplo: o que uma vaga de dev/dados costuma exigir.
TECH_VOCAB = [
    "python", "java", "javascript", "typescript", "c#", "c++", "go", "php", "sql", "scala", "kotlin",
    "postgresql", "mysql", "sql server", "oracle", "mongodb", "redis", "etl", "elt", "pandas", "numpy",
    "spark", "pyspark", "airflow", "dbt", "power bi", "tableau", "looker", "bigquery", "snowflake",
    "databricks", "data warehouse", "data lake", "kafka", "modelagem de dados", "machine learning", "nlp",
    "fastapi", "django", "flask", "node", "express", "react", "angular", "vue", "spring", "rest",
    "api rest", "graphql", "microservices", "microsservicos",
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ci/cd", "jenkins", "git", "github",
    "gitlab", "linux", "excel", "scrum", "agile", "jira", "selenium", "web scraping", "pytest",
    "llm", "hmac", "lgpd",
]


@dataclass
class Dossie:
    vaga_titulo: str
    empresa: str
    url: str
    cobertura: float
    espelhar: list = field(default_factory=list)
    gaps: list = field(default_factory=list)
    projeto_destaque: str = ""
    resumo_adaptado: str = ""


def carregar_candidato(path: str = "cv_base.yaml") -> dict:
    import yaml
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def extrair_requisitos(job) -> set:
    """Techs/keywords que o anuncio pede (titulo + descricao)."""
    return N.extract_skills(f"{job.title}\n{job.description}", TECH_VOCAB)


def _skills_candidato(candidato: dict) -> set:
    s = set(candidato.get("skills", []))
    for p in candidato.get("projetos", []):
        s |= set(p.get("tech", []))
    return s


def gerar_dossie(job, candidato: dict) -> Dossie:
    req = extrair_requisitos(job)
    minhas = _skills_candidato(candidato)
    tem = sorted(req & minhas)
    gaps = sorted(req - minhas)
    cobertura = round(100 * len(tem) / len(req), 1) if req else 0.0

    melhor, ov_max = "", 0
    for p in candidato.get("projetos", []):
        ov = len(set(p.get("tech", [])) & req)
        if ov > ov_max:
            melhor, ov_max = p.get("nome", ""), ov

    return Dossie(
        vaga_titulo=job.title, empresa=job.company, url=job.url,
        cobertura=cobertura, espelhar=tem, gaps=gaps,
        projeto_destaque=melhor, resumo_adaptado=_resumo(job, candidato, tem, melhor),
    )


def _resumo(job, candidato: dict, tem: list, projeto: str) -> str:
    partes = [f"Candidatura: {job.title}."]
    if tem:
        partes.append(f"Uso na prática: {', '.join(tem[:6])}.")
    if projeto:
        partes.append(f"Projeto mais aderente: {projeto}.")
    if candidato.get("resumo_base"):
        partes.append(candidato["resumo_base"].strip())
    return " ".join(partes)


def imprimir_dossie(d: Dossie) -> None:
    print(f"\n== {d.vaga_titulo} — {d.empresa} ==")
    print(f"  cobertura de requisitos : {d.cobertura}%")
    print(f"  espelhe no CV (você tem): {', '.join(d.espelhar) or '-'}")
    print(f"  gaps (aprender/omitir)  : {', '.join(d.gaps) or '-'}")
    print(f"  projeto a destacar      : {d.projeto_destaque or '-'}")
    print(f"  resumo sugerido         : {d.resumo_adaptado}")
    if d.url:
        print(f"  vaga                    : {d.url}")
