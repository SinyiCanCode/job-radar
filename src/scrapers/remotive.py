"""Remotive — API pública de vagas remotas (JSON, sem token).

Endpoint: https://remotive.com/api/remote-jobs?search=<termo>
Campos estáveis e documentados. É a fonte funcional de REFERÊNCIA: rode-a para
ver o pipeline inteiro com dados reais. Vagas são sempre remotas; muitas aceitam
LatAm/worldwide (bom p/ Brasil). Filtre por localização no perfil.yaml.
"""
from __future__ import annotations

from .base import BaseScraper, build_job
from ..models import Modalidade

API = "https://remotive.com/api/remote-jobs"


class RemotiveScraper(BaseScraper):
    name = "remotive"

    def fetch(self, query: str = "python", limit: int = 50):
        import requests  # lazy: pipeline com fixture roda sem requests instalado

        r = requests.get(
            API,
            params={"search": query, "limit": limit},
            headers={"User-Agent": "job-radar/0.1"},
            timeout=30,
        )
        r.raise_for_status()
        jobs = []
        for d in r.json().get("jobs", [])[:limit]:
            jobs.append(build_job(
                source=self.name,
                external_id=d.get("id"),
                title=d.get("title", ""),
                company=d.get("company_name", ""),
                url=d.get("url", ""),
                description=d.get("description", ""),
                location=d.get("candidate_required_location", ""),
                modality=Modalidade.REMOTO,          # Remotive é 100% remoto
                salary_raw=d.get("salary", "") or "",
                posted_at=d.get("publication_date"),
                raw=d,
            ))
        return jobs
