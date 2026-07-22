"""Histórico em SQLite — memória das vagas já vistas entre execuções.

Guarda cada vaga por uid (fonte:id). Numa nova busca, separa o que é NOVO
do que já apareceu antes, e deixa marcar status (aplicada/descartada).
Banco fica em saida/historico.db (ignorado pelo git).
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS vagas (
    uid TEXT PRIMARY KEY,
    source TEXT, title TEXT, company TEXT, url TEXT,
    modality TEXT, seniority TEXT, location TEXT,
    score REAL,
    primeira_vez TEXT, ultima_vez TEXT,
    status TEXT DEFAULT 'nova'
);
"""


class Historico:
    def __init__(self, db_path: str = "saida/historico.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(db_path)
        self.con.row_factory = sqlite3.Row
        self.con.executescript(SCHEMA)

    def registrar(self, vagas):
        """Registra as vagas. Retorna (novas, ja_vistas) — listas de VagaPontuada."""
        agora = datetime.now().isoformat(timespec="seconds")
        novas, vistas = [], []
        for v in vagas:
            j = v.job
            uid = j.uid()
            if self.con.execute("SELECT 1 FROM vagas WHERE uid=?", (uid,)).fetchone():
                self.con.execute("UPDATE vagas SET ultima_vez=?, score=? WHERE uid=?",
                                 (agora, v.score, uid))
                vistas.append(v)
            else:
                self.con.execute(
                    "INSERT INTO vagas (uid,source,title,company,url,modality,seniority,"
                    "location,score,primeira_vez,ultima_vez,status) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,'nova')",
                    (uid, j.source, j.title, j.company, j.url, j.modality.value,
                     j.seniority.name.lower(), j.location, v.score, agora, agora))
                novas.append(v)
        self.con.commit()
        return novas, vistas

    def marcar(self, uid: str, status: str):
        self.con.execute("UPDATE vagas SET status=? WHERE uid=?", (status, uid))
        self.con.commit()

    def uids_por_status(self, status: str) -> set:
        return {r["uid"] for r in self.con.execute("SELECT uid FROM vagas WHERE status=?", (status,))}

    def listar(self, status=None, limit=100):
        if status:
            cur = self.con.execute("SELECT * FROM vagas WHERE status=? ORDER BY score DESC LIMIT ?",
                                   (status, limit))
        else:
            cur = self.con.execute("SELECT * FROM vagas ORDER BY primeira_vez DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur]

    def stats(self) -> dict:
        d = {r["status"]: r["c"] for r in
             self.con.execute("SELECT status, COUNT(*) c FROM vagas GROUP BY status")}
        d["total"] = sum(d.values())
        return d

    def close(self):
        self.con.close()
