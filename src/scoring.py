"""Qualificação de vagas: filtros hard + score ponderado (0-100).

Calibrado para ENTRY-LEVEL:
  - falta de experiência NUNCA elimina nem penaliza;
  - Pleno/Sênior é cortado;
  - "júnior" que exige anos de experiência vira FLAG (não corte) — você decide.

Regra de ouro dos filtros: na dúvida, NÃO elimina (deixa passar com score menor).
Melhor revisar uma vaga a mais do que perder a vaga certa.
"""
from __future__ import annotations

import difflib

from . import normalize as N
from .models import Job, Modalidade, Perfil, Senioridade, VagaPontuada

DEFAULT_PESOS = {
    "skills": 0.45,
    "titulo": 0.25,
    "senioridade": 0.15,
    "modalidade": 0.10,
    "recencia": 0.05,
}


def qualificar(
    job: Job,
    perfil: Perfil,
    pesos: dict | None = None,
    bonus_max: float = 0.05,
    fuzzy_threshold: float = 0.82,
) -> VagaPontuada:
    pesos = pesos or DEFAULT_PESOS
    vp = VagaPontuada(job=job)
    texto = f"{job.title}\n{job.description}"

    # ---- filtros hard (eliminam) ----
    corte = _hard_filters(job, perfil)
    if corte:
        vp.eliminada = True
        vp.motivo_eliminacao = corte
        return vp

    # ---- componentes (cada um 0..1) ----
    matched = N.extract_skills(texto, perfil.skills, fuzzy_threshold)
    vp.matched_skills = sorted(matched)
    vp.missing_skills = sorted(set(perfil.skills) - matched)

    c = {
        "skills": _score_skills(matched, perfil),
        "titulo": _score_titulo(job.title, perfil),
        "senioridade": _score_senioridade(job.seniority, perfil),
        "modalidade": _score_modalidade(job.modality, perfil),
        "recencia": _score_recencia(job.posted_at),
    }
    total = sum(pesos.get(k, 0) * v for k, v in c.items())

    bonus = _bonus_keywords(texto, perfil, bonus_max)
    total = min(1.0, total + bonus)

    vp.score = round(total * 100, 1)
    c["bonus"] = round(bonus, 3)
    vp.breakdown = {k: round(v, 3) for k, v in c.items()}
    vp.flags = _flags(job, perfil, matched)
    return vp


def qualificar_lote(jobs, perfil, **kw) -> list[VagaPontuada]:
    """Qualifica e devolve os SOBREVIVENTES ordenados por score desc."""
    vagas = [qualificar(j, perfil, **kw) for j in jobs]
    aprovadas = [v for v in vagas if not v.eliminada]
    aprovadas.sort(key=lambda v: v.score, reverse=True)
    return aprovadas


# ------------------------------------------------------------------ filtros
def _hard_filters(job: Job, perfil: Perfil) -> str | None:
    tnorm = N.norm(job.title)

    # 1) veto por palavra no TÍTULO (ex.: sênior, coordenador)
    for v in perfil.keywords_veto:
        if N.word_in_text(v, tnorm):
            return f"veto no título: '{v}'"

    # 2) senioridade acima do alvo (só corta Pleno+; desconhecida passa)
    if perfil.senioridades_aceitas and job.seniority != Senioridade.DESCONHECIDA:
        if job.seniority not in perfil.senioridades_aceitas and job.seniority >= Senioridade.PLENO:
            return f"senioridade acima do alvo: {job.seniority.name.lower()}"

    # 3) modalidade incompatível (desconhecida passa)
    if perfil.modalidades_aceitas and job.modality != Modalidade.DESCONHECIDA:
        if job.modality not in perfil.modalidades_aceitas:
            return f"modalidade incompatível: {job.modality.value}"

    # 4) remoto restrito a fora do Brasil
    if (not perfil.aceita_remoto_global and job.modality == Modalidade.REMOTO
            and N.restringe_fora_br(job.location)):
        return f"remoto restrito a fora do BR: '{job.location}'"

    # 5) fora da área: nenhum sinal de skill NEM de título-alvo
    texto = f"{job.title}\n{job.description}"
    if not N.extract_skills(texto, perfil.skills) and _titulo_overlap(job.title, perfil) == 0:
        return "fora da área (sem match de skill/título)"

    # 6) salário abaixo do piso (só quando a vaga informa)
    if perfil.salario_minimo and job.salary_max and job.salary_max < perfil.salario_minimo:
        return f"salário abaixo do piso ({job.salary_max:.0f} < {perfil.salario_minimo:.0f})"

    return None


# ------------------------------------------------------------------ componentes
def _score_skills(matched: set, perfil: Perfil) -> float:
    if not perfil.skills:
        return 0.5
    base = len(matched) / len(set(perfil.skills))
    # obrigatória ausente => teto baixo (não zera: pode ser só ATS mal descrito)
    if set(perfil.skills_obrigatorias) - matched:
        base = min(base, 0.45)
    return min(1.0, base)


def _titulo_overlap(title: str, perfil: Perfil) -> int:
    ttok = N.sig_tokens(title)
    alvo = set()
    for t in perfil.titulos_alvo:
        alvo |= N.sig_tokens(t)
    return len(ttok & alvo)


def _score_titulo(title: str, perfil: Perfil) -> float:
    ttok = N.sig_tokens(title)
    if not ttok or not perfil.titulos_alvo:
        return 0.0
    best_cov, best_sim = 0.0, 0.0
    for t in perfil.titulos_alvo:
        atok = N.sig_tokens(t)
        if atok:
            best_cov = max(best_cov, len(ttok & atok) / len(atok))
        best_sim = max(best_sim, difflib.SequenceMatcher(None, N.norm(title), N.norm(t)).ratio())
    return round(min(1.0, 0.7 * best_cov + 0.3 * best_sim), 4)


def _score_senioridade(sv: Senioridade, perfil: Perfil) -> float:
    if not perfil.senioridades_aceitas:
        return 0.6
    if sv == Senioridade.DESCONHECIDA:
        return 0.6                       # neutro: não sabemos, não punimos
    if sv in perfil.senioridades_aceitas:
        return 1.0
    dist = min(abs(int(sv) - int(a)) for a in perfil.senioridades_aceitas)
    return max(0.0, 1.0 - 0.4 * dist)


def _score_modalidade(mv: Modalidade, perfil: Perfil) -> float:
    if not perfil.modalidades_aceitas:
        return 0.6
    if mv == Modalidade.DESCONHECIDA:
        return 0.5
    return 1.0 if mv in perfil.modalidades_aceitas else 0.0


def _score_recencia(posted) -> float:
    if not posted:
        return 0.5
    from datetime import date
    dias = (date.today() - posted).days
    if dias < 0:
        return 0.5
    if dias <= 3:
        return 1.0
    if dias <= 7:
        return 0.85
    if dias <= 14:
        return 0.65
    if dias <= 30:
        return 0.45
    return 0.25


def _bonus_keywords(texto: str, perfil: Perfil, bonus_max: float) -> float:
    hits = sum(1 for k in perfil.keywords_bonus if N.word_in_text(k, texto))
    return min(bonus_max, 0.02 * hits) if hits else 0.0


# ------------------------------------------------------------------ flags
def _flags(job: Job, perfil: Perfil, matched: set) -> list[str]:
    flags = []
    anos = N.required_years(job.description)
    entry = {Senioridade.ESTAGIO, Senioridade.TRAINEE, Senioridade.JUNIOR}
    if (job.seniority in entry or job.seniority == Senioridade.DESCONHECIDA) and anos and anos >= 1:
        flags.append(f"⚠ júnior-fake? exige {anos}+ ano(s) de experiência")
    if job.modality == Modalidade.DESCONHECIDA:
        flags.append("modalidade não detectada — confirme antes de aplicar")
    faltando_obrig = set(perfil.skills_obrigatorias) - matched
    if faltando_obrig:
        flags.append("falta skill obrigatória: " + ", ".join(sorted(faltando_obrig)))
    if any(N.word_in_text(k, f"{job.title} {job.description}") for k in perfil.keywords_bonus):
        flags.append("✓ casa com seu background")
    return flags
