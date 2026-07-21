"""Fonte offline — lê um JSON local. Usada em desenvolvimento e nos testes,
sem depender de rede. É a garantia de que o pipeline roda em qualquer lugar.
"""
from __future__ import annotations

import json
import os

from .base import BaseScraper, build_job

_DEFAULT = os.path.join(os.path.dirname(__file__), "..", "..", "data", "fixtures", "vagas_exemplo.json")


class FixtureScraper(BaseScraper):
    name = "fixture"

    def __init__(self, path: str | None = None, **opts):
        super().__init__(**opts)
        self.path = path or _DEFAULT

    def fetch(self, query: str = "", limit: int = 100):
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        jobs = []
        for i, d in enumerate(data):
            jobs.append(build_job(
                source=self.name,
                external_id=d.get("id", i),
                title=d.get("title", ""),
                company=d.get("company", ""),
                url=d.get("url", ""),
                description=d.get("description", ""),
                location=d.get("location", ""),
                salary_min=d.get("salary_min"),
                salary_max=d.get("salary_max"),
                posted_at=d.get("posted_at"),
                raw=d,
            ))
        return jobs[:limit]
