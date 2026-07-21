"""Registry de fontes. Adicionar uma fonte nova = criar o módulo e registrar aqui."""
from __future__ import annotations

from .base import BaseScraper, build_job
from .fixture import FixtureScraper
from .gupy import GupyScraper
from .linkedin import LinkedInScraper
from .remotive import RemotiveScraper

REGISTRY = {
    "fixture": FixtureScraper,
    "remotive": RemotiveScraper,
    "gupy": GupyScraper,
    "linkedin": LinkedInScraper,
}


def get_scraper(name: str, **opts) -> BaseScraper:
    if name not in REGISTRY:
        raise KeyError(f"fonte desconhecida: '{name}' (disponíveis: {list(REGISTRY)})")
    return REGISTRY[name](**opts)


__all__ = ["BaseScraper", "build_job", "get_scraper", "REGISTRY"]
