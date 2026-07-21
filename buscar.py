# -*- coding: utf-8 -*-
"""Advanced search: roda varias queries x varias fontes, junta, deduplica,
qualifica e ranqueia numa fila unica.

Uso:  py buscar.py                  # roda tudo com as QUERIES/FONTES abaixo
      py buscar.py --top 40         # mostra mais resultados
      py buscar.py --fontes gupy    # so uma fonte

Edite QUERIES e FONTES pra ajustar sua busca.
"""
from __future__ import annotations

import argparse
import os

from src.models import Perfil
from src.pipeline import carregar_config, coletar
from src.scoring import DEFAULT_PESOS, qualificar
from src.storage import dedupe, salvar_csv, salvar_json

# ------------------ ajuste sua busca aqui ------------------
QUERIES = [
    "estágio desenvolvimento",
    "estágio desenvolvedor",
    "estágio python",
    "estágio backend",
    "estágio dados",
    "estágio analista de dados",
    "estágio engenharia de dados",
    "estágio BI",
    "estagiário TI",
]
FONTES = ["gupy", "remotive"]
LIMITE_POR_QUERY = 30
# -----------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description="Advanced search de vagas")
    ap.add_argument("--fontes", nargs="+", default=FONTES)
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--limit", type=int, default=LIMITE_POR_QUERY)
    ap.add_argument("--perfil", default="perfil.yaml")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--out", default="saida")
    args = ap.parse_args()

    perfil = Perfil.from_yaml(args.perfil)
    cfg = carregar_config(args.config)
    kw = dict(
        pesos=cfg.get("pesos", DEFAULT_PESOS),
        bonus_max=cfg.get("bonus_keywords_max", 0.05),
        fuzzy_threshold=cfg.get("fuzzy_threshold", 0.82),
    )
    minimo = cfg.get("score_minimo_fila", 0)

    brutas = []
    for q in QUERIES:
        print(f">>> buscando: '{q}'")
        brutas += coletar(args.fontes, q, limit=args.limit)

    unicas = dedupe(brutas)
    scored = [qualificar(j, perfil, **kw) for j in unicas]
    aprovadas = sorted((v for v in scored if not v.eliminada),
                       key=lambda v: v.score, reverse=True)
    fila = [v for v in aprovadas if v.score >= minimo]

    print("\n" + "=" * 62)
    print(f"coletado: {len(brutas)}  |  unicas: {len(unicas)}  |  "
          f"eliminadas: {len(scored) - len(aprovadas)}  |  FILA: {len(fila)}")
    print("=" * 62)

    for i, v in enumerate(fila[:args.top], 1):
        j = v.job
        print(f"\n{i:>2}. [{v.score:5.1f}] {j.title}  -  {j.company}")
        print(f"      {j.modality.value} - {j.seniority.name.lower()} - {j.location or '?'} - {j.source}")
        if v.matched_skills:
            print(f"      skills: {', '.join(v.matched_skills)}")
        for fl in v.flags:
            print(f"      {fl}")
        print(f"      {j.url}")

    os.makedirs(args.out, exist_ok=True)
    salvar_json(fila, os.path.join(args.out, "busca.json"))
    salvar_csv(fila, os.path.join(args.out, "busca.csv"))
    print(f"\nFila completa salva em {args.out}/busca.json e {args.out}/busca.csv")


if __name__ == "__main__":
    main()
