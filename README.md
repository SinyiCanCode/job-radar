# job-radar

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/tests-9%20passing-brightgreen.svg)

**Agregador e qualificador de vagas.** Coleta vagas de várias plataformas, normaliza tudo num formato único e pontua cada uma pela aderência ao *seu* perfil — pra você parar de garimpar e ler só o que vale a pena.

---

## O problema

Procurar vaga de estágio ou júnior é um funil de tempo perdido. Você abre cinco plataformas, aplica os mesmos filtros em cada uma, lê trinta descrições — e no fim vinte e oito não servem: a "júnior" que exige três anos de experiência, a "remota" que era presencial em outro estado, a sênior que o filtro da plataforma não separou. O trabalho é repetitivo, manual e desanima.

## A solução

O `job-radar` faz a triagem por você. Ele coleta as vagas, entende cada uma (modalidade, senioridade, skills, localização) e devolve uma **fila priorizada** por quanto cada vaga combina com o seu perfil. O que é claramente incompatível é cortado com o motivo explícito. Você lê cinco vagas em vez de cinquenta.

## Exemplo

```
>>> buscando: 'estágio dados'
  [gupy] 24 vagas
  [remotive] 12 vagas

==============================================================
coletado: 216  |  únicas: 47  |  eliminadas: 41  |  FILA: 6
==============================================================

 1. [ 78.5] Estágio em Engenharia de Dados  -  Contabilizei
      remoto - estagio - Remoto/SP - gupy
      skills: python, sql, etl, git
      ✓ casa com seu background
      https://contabilizei.gupy.io/job/...

 2. [ 57.3] Desenvolvedor Python Júnior  -  SoftX
      remoto - junior - Remoto - gupy
      skills: python
      ⚠ júnior-fake? exige 3+ ano(s) de experiência
      https://...

── ELIMINADAS (41) ──
   ✗ Analista de Dados Sênior — Flora   (veto no título: 'sênior')
   ✗ Analista de Dados Jr — Stefanini   (modalidade incompatível: presencial)
   ✗ Junior Data Analyst — GlobalCorp   (remoto restrito a fora do BR)
```

A vaga certa no topo. A "júnior" que pede 3 anos, sinalizada em vez de escondida. O resto, cortado com o porquê.

## Como funciona

Duas etapas independentes:

**1. Coleta + normalização** — cada fonte (`src/scrapers/`) baixa as vagas e converte para o mesmo objeto `Job` (título, empresa, modalidade, senioridade, localização, descrição, link). Da normalização em diante, a origem não importa.

**2. Qualificação** (`src/scoring.py`) — em dois passos:

- **Filtros hard** eliminam o incompatível (modalidade errada, senioridade acima do alvo, fora da área, remoto restrito a outro país, veto no título).
- **Score 0–100** ordena o que sobrou por aderência: skills, título, senioridade, modalidade, recência, mais um bônus quando a vaga bate com o seu histórico.

O resultado é uma fila. O envio do currículo continua com você — é onde mora o risco de ban e onde um CV adaptado faz a diferença.

## Instalação

```bash
git clone https://github.com/SinyiCanCode/job-radar.git
cd job-radar
pip install -r requirements.txt
```

## Uso

**Busca única** (uma fonte, um termo):

```bash
python main.py --fontes gupy --query "analista de dados" --verbose
python main.py --fontes remotive --query python --limit 20
```

**Advanced search** (várias queries × várias fontes, junta e deduplica numa fila só):

```bash
python buscar.py
```

As queries ficam no topo do `buscar.py` — edite pra mirar o que você quiser. Toda execução salva a fila em `saida/*.csv` (abre no Excel) e `saida/*.json`.

## Fontes

| Fonte | Status | Observação |
|-------|--------|------------|
| `gupy` | ✅ funcional | Plataforma de ATS mais comum no Brasil. Endpoint público do portal de candidatos. |
| `remotive` | ✅ funcional | API pública de vagas remotas (internacional/LatAm). |
| `fixture` | ✅ offline | Dataset local pra desenvolvimento e testes, sem rede. |
| `linkedin` | ⛔ desativado | ToS proíbe scraping automatizado. Prefira coletar manual e colar numa fixture. |

## Calibrando pro seu perfil

Todo o comportamento vem de dois arquivos de config, sem tocar no código:

- **`perfil.yaml`** — seu alvo: `titulos_alvo`, `skills`, `senioridades_aceitas` (estágio/júnior…), `modalidades_aceitas` (remoto/híbrido/presencial), `keywords_bonus` (seu diferencial) e `keywords_veto` (corta no título).
- **`config.yaml`** — pesos do score, `fuzzy_threshold` e `score_minimo_fila`.

## Adicionar uma fonte nova

1. Crie `src/scrapers/minhafonte.py` com uma classe que herda `BaseScraper` e implementa `fetch()`, devolvendo `Job` via `build_job(...)`.
2. Registre em `src/scrapers/__init__.py`.
3. `python main.py --fontes minhafonte`.

## Testes

```bash
python -m pytest tests/ -v
```

Cobrem o motor de qualificação (vaga ideal pontua alto; presencial/sênior/fora-da-área/geo são eliminadas; júnior-fake vira flag; ranqueamento por aderência) e o pipeline end-to-end.

## Roadmap

- Buscar a descrição completa por vaga pra afinar o match de skills.
- Persistir histórico (SQLite) pra não repontuar o que já viu.
- Mais fontes BR (Programathor, Trampos, Remotar).
- Notificação diária com a fila nova por e-mail/Telegram.

## Uso responsável

O `job-radar` usa endpoints e APIs **públicos**, sem burlar autenticação nem captcha, e sem disparar candidaturas automáticas — a decisão de aplicar é sempre humana. É uma ferramenta pessoal de organização, não de spam. Use com parcimônia, respeite os Termos de Uso de cada plataforma e o `robots.txt`.

## Licença

[MIT](LICENSE) © 2026 Francisco Lima Santos
