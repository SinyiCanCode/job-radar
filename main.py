"""CLI do job-radar.

Exemplos:
  python main.py                                   # roda com a fixture (offline)
  python main.py --fontes remotive --query python  # fonte real remota
  python main.py --fontes gupy remotive --query "analista de dados" --limit 40
  python main.py --verbose                         # mostra também as eliminadas
"""
from __future__ import annotations

import argparse
import os

from src.pipeline import rodar
from src.storage import salvar_csv, salvar_json


def _print_fila(fila, top):
    if not fila:
        print("(fila vazia)")
        return
    print(f"── FILA PRIORIZADA (top {min(top, len(fila))} de {len(fila)}) ──")
    for i, v in enumerate(fila[:top], 1):
        j = v.job
        print(f"\n{i:>2}. [{v.score:5.1f}] {j.title}  —  {j.company}")
        print(f"      {j.modality.value} · {j.seniority.name.lower()} · {j.location or '?'} · fonte:{j.source}")
        if v.matched_skills:
            print(f"      skills: {', '.join(v.matched_skills)}")
        for fl in v.flags:
            print(f"      {fl}")
        print(f"      {j.url}")


def _print_eliminadas(elim):
    print(f"\n── ELIMINADAS ({len(elim)}) ──")
    for v in elim:
        print(f"   ✗ {v.job.title} — {v.job.company}  ({v.motivo_eliminacao})")


def main():
    ap = argparse.ArgumentParser(description="Agregador + qualificador de vagas")
    ap.add_argument("--fontes", nargs="+", default=["fixture"],
                    help="fixture | remotive | gupy | linkedin")
    ap.add_argument("--query", default="dados")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--perfil", default="perfil.yaml")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--out", default="saida")
    ap.add_argument("--verbose", action="store_true", help="mostra as vagas eliminadas e o motivo")
    args = ap.parse_args()

    print(f"Coletando de {args.fontes} | query='{args.query}' | limite={args.limit}")
    res = rodar(perfil_path=args.perfil, config_path=args.config,
                fontes=args.fontes, query=args.query, limit=args.limit)

    print(f"\nColetadas: {res.coletadas} | Únicas: {res.unicas} | "
          f"Eliminadas: {len(res.eliminadas)} | Fila: {len(res.fila)} | "
          f"Abaixo do mínimo: {len(res.abaixo_minimo)}\n")
    _print_fila(res.fila, args.top)
    if args.verbose:
        _print_eliminadas(res.eliminadas)

    os.makedirs(args.out, exist_ok=True)
    salvar_json(res.fila, os.path.join(args.out, "fila.json"))
    salvar_csv(res.fila, os.path.join(args.out, "fila.csv"))
    print(f"\n✓ Salvo em {args.out}/fila.json e {args.out}/fila.csv")


if __name__ == "__main__":
    main()
