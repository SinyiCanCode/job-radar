"""Normalização: converte texto cru de qualquer fonte em sinais estruturados.

Tudo que "entende" linguagem natural (modalidade, senioridade, skills) mora aqui,
isolado do motor de score. Assim dá pra melhorar a detecção sem tocar na pontuação.
"""
from __future__ import annotations

import difflib
import re
import unicodedata
from datetime import date, datetime
from typing import Optional

from .models import Modalidade, Senioridade


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm(s) -> str:
    """lower, sem acento, espaços colapsados."""
    if s is None:
        return ""
    return re.sub(r"\s+", " ", strip_accents(str(s)).lower()).strip()


_TOKEN_RX = re.compile(r"[a-z0-9\+\.#]+")


def tokens(s) -> set:
    return set(_TOKEN_RX.findall(norm(s)))


STOPWORDS = {
    "de", "da", "do", "dos", "das", "e", "em", "para", "com", "a", "o", "os", "as",
    "jr", "pj", "clt", "i", "ii", "iii", "the", "and", "of", "in", "-", "–", "para",
}


def sig_tokens(s) -> set:
    """Tokens significativos (sem stopwords, len>1)."""
    return {t for t in tokens(s) if t not in STOPWORDS and len(t) > 1}


def word_in_text(word: str, text: str) -> bool:
    """Match por limite de palavra p/ 1 token; substring p/ expressões multi-palavra."""
    w = norm(word)
    if not w:
        return False
    if " " in w or any(c in w for c in ".+#"):
        return w in norm(text)
    return re.search(rf"(?<![a-z0-9]){re.escape(w)}(?![a-z0-9])", norm(text)) is not None


# ---------------------------------------------------------------- skills
# Cada skill do perfil pode aparecer sob várias grafias no anúncio.
SKILL_SYNONYMS = {
    "postgresql": ["postgresql", "postgres", "postgre", "psql"],
    "api rest": ["api rest", "apis rest", "rest api", "restful", "rest"],
    "javascript": ["javascript", "js"],
    "node": ["node", "node.js", "nodejs"],
    "react": ["react", "react.js", "reactjs"],
    "modelagem de dados": ["modelagem de dados", "modelagem relacional", "data modeling", "modelagem"],
    "etl": ["etl", "elt"],
    "excel": ["excel", "planilhas"],
    "docker": ["docker", "container", "containers", "conteiner"],
    "git": ["git", "github", "gitlab"],
    "power bi": ["power bi", "powerbi", "power-bi"],
}


def _expand_skill(skill: str) -> list[str]:
    return SKILL_SYNONYMS.get(norm(skill), [norm(skill)])


def skill_in_text(skill: str, text: str, threshold: float = 0.82) -> bool:
    t = norm(text)
    for pat in _expand_skill(skill):
        p = norm(pat)
        if " " in p or any(c in p for c in ".+#"):
            if p in t:
                return True
        elif re.search(rf"(?<![a-z0-9]){re.escape(p)}(?![a-z0-9])", t):
            return True
    # fuzzy só na forma canônica de token único — pega erros de digitação
    canon = norm(skill)
    if len(canon) >= 4 and " " not in canon:
        for tok in tokens(t):
            if len(tok) >= 4 and difflib.SequenceMatcher(None, canon, tok).ratio() >= threshold:
                return True
    return False


def extract_skills(text: str, vocab, threshold: float = 0.82) -> set:
    """Subconjunto de `vocab` (skills do perfil) presente no texto."""
    return {s for s in vocab if skill_in_text(s, text, threshold)}


# ---------------------------------------------------------------- modalidade
_RX_HIBRIDO = re.compile(r"\b(hibrido|hybrid)\b")
_RX_REMOTO = re.compile(r"\b(remoto|remote|home\s*office|anywhere|teletrabalho|100%?\s*remoto)\b")
_RX_PRESENCIAL = re.compile(r"\b(presencial|on-?site|no escritorio|100%?\s*presencial)\b")


def detect_modality(*parts) -> Modalidade:
    t = norm(" ".join(p for p in parts if p))
    if _RX_HIBRIDO.search(t):
        return Modalidade.HIBRIDO
    if _RX_REMOTO.search(t):
        return Modalidade.REMOTO
    if _RX_PRESENCIAL.search(t):
        return Modalidade.PRESENCIAL
    return Modalidade.DESCONHECIDA


def restringe_fora_br(location: str) -> bool:
    """True se a vaga remota exige residência fora do Brasil (ex.: 'USA Only')."""
    l = norm(location)
    if not l:
        return False
    if any(x in l for x in ["brasil", "brazil", "worldwide", "anywhere", "global",
                            "latam", "latin america", "americas", "remoto"]):
        return False
    if "only" in l or "apenas" in l or "somente" in l:
        return True
    return any(x in l for x in ["usa", "united states", "europe", "emea", "uk",
                                "canada", "india", "germany", "portugal only"])


# ---------------------------------------------------------------- senioridade
_SEN_PATTERNS = [
    (Senioridade.ESTAGIO, re.compile(r"\b(estagio|estagiario|intern|internship)\b")),
    (Senioridade.TRAINEE, re.compile(r"\b(trainee)\b")),
    (Senioridade.SENIOR, re.compile(r"\b(senior|sr|especialista|lead|principal|staff)\b")),
    (Senioridade.PLENO, re.compile(r"\b(pleno|mid-?level|middle)\b")),
    (Senioridade.JUNIOR, re.compile(r"\b(junior|jr|entry-?level|entry|iniciante|assistente|auxiliar)\b")),
]


def detect_seniority(title: str, description: str = "") -> Senioridade:
    tt = norm(title)
    for sen, rx in _SEN_PATTERNS:      # título tem prioridade
        if rx.search(tt):
            return sen
    td = norm(description)
    for sen, rx in _SEN_PATTERNS:
        if rx.search(td):
            return sen
    return Senioridade.DESCONHECIDA


# ---------------------------------------------------------------- datas / anos
def parse_date(value) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s[:len(fmt) + 2].strip(), fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "")).date()
    except Exception:
        return None


# Só dispara com "X+ anos" ou "X anos de experiência" — evita falso positivo tipo "há 10 anos".
_YEARS_RX = re.compile(
    r"(\d+)\s*\+\s*anos?"
    r"|(\d+)\s*anos?\s+de\s+experi"
    r"|experi\w*\s+(?:de\s+|m[ií]nima\s+de\s+)?(\d+)\s*anos?"
)


def required_years(text: str) -> Optional[int]:
    if not text:
        return None
    yrs = []
    for m in _YEARS_RX.finditer(norm(text)):
        for g in m.groups():
            if g and 1 <= int(g) <= 20:
                yrs.append(int(g))
    return max(yrs) if yrs else None
