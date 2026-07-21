"""Interface comum a toda fonte de vagas.

Regra: um scraper coleta o formato cru da plataforma e devolve SEMPRE uma lista
de `Job` já normalizado. Nenhuma lógica de score mora aqui.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..models import Job, Modalidade, Senioridade


class BaseScraper(ABC):
    name: str = "base"

    def __init__(self, **opts):
        self.opts = opts

    @abstractmethod
    def fetch(self, query: str, limit: int = 50) -> list[Job]:
        """Coleta vagas e devolve já como `Job` normalizado."""
        raise NotImplementedError


def build_job(
    source: str,
    external_id,
    title: str,
    company: str,
    url: str,
    description: str = "",
    location: str = "",
    modality: Optional[Modalidade] = None,
    seniority: Optional[Senioridade] = None,
    salary_min=None,
    salary_max=None,
    salary_raw: str = "",
    posted_at=None,
    raw: dict | None = None,
) -> Job:
    """Monta um Job preenchendo modalidade/senioridade/data automaticamente
    quando o scraper não conseguiu extrair explicitamente."""
    from .. import normalize as N

    desc = description or ""
    return Job(
        source=source,
        external_id=str(external_id),
        title=title or "",
        company=company or "",
        url=url or "",
        description=desc,
        location=location or "",
        modality=modality or N.detect_modality(title, location, desc),
        seniority=seniority or N.detect_seniority(title, desc),
        salary_min=salary_min,
        salary_max=salary_max,
        salary_raw=salary_raw,
        posted_at=N.parse_date(posted_at),
        raw=raw or {},
    )
