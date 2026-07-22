"""Testes do histórico SQLite."""
from __future__ import annotations
import os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.models import Job, VagaPontuada   # noqa: E402
from src.historico import Historico        # noqa: E402


def _vp(i, score=80.0):
    return VagaPontuada(job=Job(source="t", external_id=str(i), title="V", company="C", url="u"), score=score)


def test_novo_vira_visto():
    h = Historico(tempfile.mktemp(suffix=".db"))
    novas, vistas = h.registrar([_vp(1), _vp(2)])
    assert len(novas) == 2 and len(vistas) == 0
    novas2, vistas2 = h.registrar([_vp(1), _vp(3)])       # 1 já visto, 3 novo
    assert len(novas2) == 1 and len(vistas2) == 1
    assert novas2[0].job.uid() == "t:3"
    h.close()


def test_marcar_status():
    h = Historico(tempfile.mktemp(suffix=".db"))
    h.registrar([_vp(1)])
    h.marcar("t:1", "aplicada")
    assert "t:1" in h.uids_por_status("aplicada")
    assert h.stats()["total"] == 1
    h.close()


if __name__ == "__main__":
    fns = [g for n, g in sorted(globals().items()) if n.startswith("test_") and callable(g)]
    for fn in fns:
        fn(); print("PASS", fn.__name__)
    print(f"{len(fns)} ok")
