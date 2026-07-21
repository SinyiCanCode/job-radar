# -*- coding: utf-8 -*-
"""adaptar.py — Fase 2: dossiê de adaptação do CV pra cada vaga da fila.

Roda a busca, qualifica, e pra cada vaga aprovada mostra o que ajustar no CV.

Uso:  py adaptar.py --fontes gupy --query "estágio dados" --top 5
      py adaptar.py --fontes fixture              # offline, pra testar
"""
from __future__ import annotations

import argparse

from src.models import Perfil
from src.pipeline import carregar_config, coletar
from src.scoring import DEFAULT_PESOS, qualificar
from src.storage import dedupe
from src.tailor import carregar_candidato, gerar_dossie, imprimir_dossie


def main():
    ap = argparse.ArgumentParser(description="Adapta o CV a cada vaga da fila")
    ap.add_argument("--fontes", nargs="+", default=["gupy"])
    ap.add_argument("--query", default="estágio dados")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--perfil", default="perfil.yaml")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--cv", default="cv_base.yaml")
    args = ap.parse_args()

    perfil = Perfil.from_yaml(args.perfil)
    cfg = carregar_config(args.config)
    kw = dict(pesos=cfg.get("pesos", DEFAULT_PESOS),
              bonus_max=cfg.get("bonus_keywords_max", 0.05),
              fuzzy_threshold=cfg.get("fuzzy_threshold", 0.82))
    minimo = cfg.get("score_minimo_fila", 0)
    candidato = carregar_candidato(args.cv)

    brutas = coletar(args.fontes, args.query, limit=args.limit)
    unicas = dedupe(brutas)
    fila = sorted((qualificar(j, perfil, **kw) for j in unicas),
                  key=lambda v: v.score, reverse=True)
    fila = [v for v in fila if not v.eliminada and v.score >= minimo][:args.top]

    print(f"\n{len(fila)} vaga(s) na fila — dossiê de adaptação do CV:")
    print("=" * 62)
    for v in fila:
        imprimir_dossie(gerar_dossie(v.job, candidato))


if __name__ == "__main__":
    main()
