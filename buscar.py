# -*- coding: utf-8 -*-
"""Advanced search: roda varias queries x varias fontes, junta, deduplica,
qualifica e ranqueia numa fila unica. Guarda historico (SQLite) e destaca
o que e NOVO entre execucoes.

Uso:  py buscar.py                  # roda tudo
      py buscar.py --somente-novas  # so vagas nunca vistas antes
      py buscar.py --sem-historico  # ignora o banco
"""
from __future__ import annotations

import argparse
import os

from src.historico import Historico
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
    ap.add_argument("--db", default="saida/historico.db")
    ap.add_argument("--somente-novas", action="store_true", help="mostra só vagas nunca vistas antes")
    ap.add_argument("--sem-historico", action="store_true", help="não usa o banco de histórico")
    args = ap.parse_args()

    perfil = Perfil.from_yaml(args.perfil)
    cfg = carregar_config(args.config)
    kw = dict(pesos=cfg.get("pesos", DEFAULT_PESOS),
              bonus_max=cfg.get("bonus_keywords_max", 0.05),
              fuzzy_threshold=cfg.get("fuzzy_threshold", 0.82))
    minimo = cfg.get("score_minimo_fila", 0)

    brutas = []
    for q in QUERIES:
        print(f">>> buscando: '{q}'")
        brutas += coletar(args.fontes, q, limit=args.limit)

    unicas = dedupe(brutas)
    scored = [qualificar(j, perfil, **kw) for j in unicas]
    aprovadas = sorted((v for v in scored if not v.eliminada), key=lambda v: v.score, reverse=True)
    fila = [v for v in aprovadas if v.score >= minimo]

    novas_uids = set()
    if not args.sem_historico:
        h = Historico(args.db)
        novas, _ = h.registrar(fila)
        novas_uids = {v.job.uid() for v in novas}
        h.close()

    mostrar = [v for v in fila if v.job.uid() in novas_uids] if args.somente_novas else fila

    extra = f"  |  NOVAS: {len(novas_uids)}" if not args.sem_historico else ""
    print("\n" + "=" * 62)
    print(f"coletado: {len(brutas)}  |  unicas: {len(unicas)}  |  "
          f"eliminadas: {len(scored) - len(aprovadas)}  |  FILA: {len(fila)}{extra}")
    print("=" * 62)

    for i, v in enumerate(mostrar[:args.top], 1):
        j = v.job
        tag = "  [NOVA]" if j.uid() in novas_uids else ""
        print(f"\n{i:>2}. [{v.score:5.1f}]{tag} {j.title}  -  {j.company}")
        print(f"      {j.modality.value} - {j.seniority.name.lower()} - {j.location or '?'} - {j.source}")
        if v.matched_skills:
            print(f"      skills: {', '.join(v.matched_skills)}")
        for fl in v.flags:
            print(f"      {fl}")
        print(f"      {j.url}")

    os.makedirs(args.out, exist_ok=True)
    salvar_json(fila, os.path.join(args.out, "busca.json"))
    salvar_csv(fila, os.path.join(args.out, "busca.csv"))
    print(f"\nFila salva em {args.out}/busca.json e {args.out}/busca.csv")


if __name__ == "__main__":
    main()
