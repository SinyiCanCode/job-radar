"""Gupy - portal publico de vagas (a plataforma de ATS mais comum no Brasil).

Endpoint real do portal de candidatos (descoberto via DevTools):
  GET https://employability-portal.gupy.io/api/v1/jobs?jobName=<termo>&limit=<n>&offset=<n>

A listagem traz titulo, empresa, local, modalidade E a descricao completa da
vaga (campo 'description') - o que permite o match de skills de verdade.
Os nomes de campo sao resolvidos de forma defensiva (varios aliases).
"""
from __future__ import annotations

from .base import BaseScraper, build_job
from ..models import Modalidade

API = "https://employability-portal.gupy.io/api/v1/jobs"
PAGE = 12  # limite por pagina observado na API


def _first(d, *keys, default=None):
    for k in keys:
        if d.get(k) not in (None, ""):
            return d[k]
    return default


def _map_workplace(v, is_remote=None):
    if is_remote is True:
        return Modalidade.REMOTO
    m = (v or "").lower()
    if "remote" in m or "remoto" in m:
        return Modalidade.REMOTO
    if "hybrid" in m or "hibrido" in m:
        return Modalidade.HIBRIDO
    if "onsite" in m or "on-site" in m or "presencial" in m:
        return Modalidade.PRESENCIAL
    return None


class GupyScraper(BaseScraper):
    name = "gupy"

    def fetch(self, query="dados", limit=50):
        import requests
        jobs, offset = [], 0
        while len(jobs) < limit:
            r = requests.get(
                API,
                params={"jobName": query, "limit": PAGE, "offset": offset},
                headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
                timeout=30,
            )
            r.raise_for_status()
            payload = r.json()
            data = payload.get("data") or payload.get("jobs") or payload.get("results") or []
            if not data:
                break
            for d in data:
                cidade = _first(d, "city", "cityName", default="")
                estado = _first(d, "state", "stateName", "uf", default="")
                jobs.append(build_job(
                    source=self.name,
                    external_id=_first(d, "id", "jobId", "publicId", default=_first(d, "jobUrl", default="")),
                    title=_first(d, "name", "title", "jobName", default=""),
                    company=_first(d, "careerPageName", "companyName", "company", default=""),
                    url=_first(d, "jobUrl", "url", "careerPageUrl", default=""),
                    description=_first(d, "description", "jobDescription", default=""),
                    location=" ".join(str(x) for x in [cidade, estado] if x),
                    modality=_map_workplace(_first(d, "workplaceType", "type", default=""), d.get("isRemoteWork")),
                    posted_at=_first(d, "publishedDate", "publishedAt", "createdAt", default=None),
                    raw=d,
                ))
                if len(jobs) >= limit:
                    break
            offset += PAGE
        return jobs[:limit]
