"""Diagnostico da API de vagas do Gupy (endpoint real do portal de candidatos).
Uso:  py diag_gupy.py   -> cole TODO o output no chat.
"""
import json, requests

URL = "https://employability-portal.gupy.io/api/v1/jobs"
PARAMS = {"jobName": "analista de dados", "limit": 5, "offset": 0}
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

print("GET", URL, PARAMS)
r = requests.get(URL, params=PARAMS, headers=HEADERS, timeout=25)
print("STATUS:", r.status_code, "| CT:", r.headers.get("content-type"))
d = r.json()
print("CHAVES DO TOPO:", list(d.keys()) if isinstance(d, dict) else f"lista[{len(d)}]")
items = (d.get("data") or d.get("jobs") or d.get("results") or []) if isinstance(d, dict) else d
print("N DE ITENS:", len(items))
if items:
    print("CHAVES DO 1o ITEM:", list(items[0].keys()))
    print("--- 1o ITEM COMPLETO ---")
    print(json.dumps(items[0], ensure_ascii=False, indent=2))
