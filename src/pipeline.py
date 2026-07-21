"""Orquestração: coleta (N fontes) -> dedupe -> qualifica -> ranqueia."""
from __future__ import annotations

from dataclasses import dataclass, field

import yaml

from .models import Perfil, VagaPontuada
from .scoring import DEFAULT_PESOS, qualificar
from .scrapers import get_scraper
from .storage import dedupe


@dataclass
class Resultado:
    coletadas: int = 0
    unicas: int = 0
    fila: list[VagaPontuada] = field(default_factory=list)          # aprovadas, score >= mínimo
    abaixo_minimo: list[VagaPontuada] = field(default_factory=list)
    eliminadas: list[VagaPontuada] = field(default_factory=list)


def carregar_config(path: str = "config.yaml") -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def coletar(fontes, query: str, limit: int = 50, scraper_opts: dict | None = None) -> list:
    scraper_opts = scraper_opts or {}
    jobs = []
    for nome in fontes:
        try:
            sc = get_scraper(nome, **scraper_opts.get(nome, {}))
            got = sc.fetch(query=query, limit=limit)
            jobs.extend(got)
            print(f"  [{nome}] {len(got)} vagas")
        except Exception as e:                       # rede/fonte fora não derruba as outras
            print(f"  [{nome}] ERRO: {e}")
    return jobs


def rodar(perfil_path="perfil.yaml", config_path="config.yaml",
          fontes=("fixture",), query="dados", limit=50) -> Resultado:
    perfil = Perfil.from_yaml(perfil_path)
    cfg = carregar_config(config_path)
    kw = dict(
        pesos=cfg.get("pesos", DEFAULT_PESOS),
        bonus_max=cfg.get("bonus_keywords_max", 0.05),
        fuzzy_threshold=cfg.get("fuzzy_threshold", 0.82),
    )
    minimo = cfg.get("score_minimo_fila", 0)

    brutas = coletar(fontes, query, limit)
    unicas = dedupe(brutas)
    todas = [qualificar(j, perfil, **kw) for j in unicas]

    aprovadas = sorted((v for v in todas if not v.eliminada),
                       key=lambda v: v.score, reverse=True)
    return Resultado(
        coletadas=len(brutas),
        unicas=len(unicas),
        fila=[v for v in aprovadas if v.score >= minimo],
        abaixo_minimo=[v for v in aprovadas if v.score < minimo],
        eliminadas=[v for v in todas if v.eliminada],
    )
