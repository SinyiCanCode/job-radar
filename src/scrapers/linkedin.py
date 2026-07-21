"""LinkedIn — ESQUELETO com Playwright (desativado por padrão).

⚠ LEIA ANTES DE HABILITAR:
O LinkedIn PROÍBE scraping automatizado nos Termos de Uso e tem anti-bot
agressivo: detecção de automação, auth wall, rate limit e BAN de conta. Um bot
disparando aqui é o caminho mais rápido de perder sua conta pessoal.

Recomendação prática: garimpe no LinkedIn manualmente e cole os links que achar
numa fixture .json (mesmo formato de data/fixtures/vagas_exemplo.json) — o
pipeline pontua igual, sem risco. Deixe a automação de coleta pro Gupy/Remotive.

Se ainda assim quiser automatizar, faça por sua conta e risco: logado com sua
conta, headless=False, com pausas humanas, e sabendo que os seletores mudam
com frequência.
"""
from __future__ import annotations

from .base import BaseScraper


class LinkedInScraper(BaseScraper):
    name = "linkedin"

    def fetch(self, query: str = "analista de dados junior", limit: int = 25):
        raise NotImplementedError(
            "Scraper do LinkedIn desativado por padrão (ToS + anti-bot). "
            "Leia os avisos no topo de src/scrapers/linkedin.py. Prefira coletar "
            "manualmente e usar uma fixture .json."
        )

    # --- Esqueleto de referência (NÃO habilitado) ---------------------------
    # def _fetch_playwright(self, query, limit):
    #     from playwright.sync_api import sync_playwright
    #     with sync_playwright() as p:
    #         browser = p.chromium.launch(headless=False)   # visível reduz detecção
    #         page = browser.new_page()
    #         page.goto(f"https://www.linkedin.com/jobs/search/?keywords={query}")
    #         # login manual -> scroll incremental -> extrair cards de vaga
    #         # seletores mudam com frequência; inspecione e ajuste.
    #         cards = page.query_selector_all("div.job-card-container")
    #         ...
    #         browser.close()
