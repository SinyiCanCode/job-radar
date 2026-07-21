"""Modelos de dados do job-radar.

Job          = uma vaga JÁ normalizada (formato único, independente da fonte).
Perfil       = o alvo do candidato, usado pela camada de qualificação.
VagaPontuada = Job + resultado da qualificação (score, flags, motivo de corte).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum, IntEnum
from typing import Optional


class Modalidade(Enum):
    REMOTO = "remoto"
    HIBRIDO = "hibrido"
    PRESENCIAL = "presencial"
    DESCONHECIDA = "desconhecida"


class Senioridade(IntEnum):
    # IntEnum para medir "distância" entre níveis (ex.: junior->pleno = 1).
    ESTAGIO = 0
    TRAINEE = 1
    JUNIOR = 2
    PLENO = 3
    SENIOR = 4
    DESCONHECIDA = 99


@dataclass
class Job:
    """Vaga normalizada. Toda fonte converte para este formato."""
    source: str
    external_id: str
    title: str
    company: str
    url: str
    description: str = ""
    modality: Modalidade = Modalidade.DESCONHECIDA
    location: str = ""
    seniority: Senioridade = Senioridade.DESCONHECIDA
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_raw: str = ""
    posted_at: Optional[date] = None
    collected_at: datetime = field(default_factory=datetime.utcnow)
    raw: dict = field(default_factory=dict)

    def uid(self) -> str:
        """Chave de deduplicação estável entre execuções."""
        return f"{self.source}:{self.external_id}"


@dataclass
class Perfil:
    """Alvo do candidato. Carregado de perfil.yaml."""
    titulos_alvo: list[str]
    skills: list[str]
    skills_obrigatorias: list[str] = field(default_factory=list)
    senioridades_aceitas: list[Senioridade] = field(default_factory=list)
    modalidades_aceitas: list[Modalidade] = field(default_factory=list)
    localizacao: str = ""
    aceita_remoto_global: bool = True
    salario_minimo: Optional[float] = None
    keywords_bonus: list[str] = field(default_factory=list)
    keywords_veto: list[str] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: str) -> "Perfil":
        import yaml
        with open(path, encoding="utf-8") as f:
            d = yaml.safe_load(f) or {}
        return cls(
            titulos_alvo=[t.lower() for t in d.get("titulos_alvo", [])],
            skills=[s.lower() for s in d.get("skills", [])],
            skills_obrigatorias=[s.lower() for s in d.get("skills_obrigatorias", [])],
            senioridades_aceitas=[Senioridade[s.upper()] for s in d.get("senioridades_aceitas", [])],
            modalidades_aceitas=[Modalidade(m.lower()) for m in d.get("modalidades_aceitas", [])],
            localizacao=d.get("localizacao", ""),
            aceita_remoto_global=bool(d.get("aceita_remoto_global", True)),
            salario_minimo=d.get("salario_minimo"),
            keywords_bonus=[k.lower() for k in d.get("keywords_bonus", [])],
            keywords_veto=[k.lower() for k in d.get("keywords_veto", [])],
        )


@dataclass
class VagaPontuada:
    """Job + resultado da qualificação."""
    job: Job
    score: float = 0.0                      # 0-100
    breakdown: dict = field(default_factory=dict)
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    eliminada: bool = False
    motivo_eliminacao: str = ""
