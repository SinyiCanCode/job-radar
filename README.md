# job-radar

Agregador + qualificador de vagas. Coleta vagas de várias plataformas, normaliza
para um formato único e pontua cada uma pela aderência ao seu perfil — pra você
gastar tempo só nas que valem a pena. Calibrado para **estágio / júnior em dados**,
mas tudo é configurável por arquivo, sem tocar no código.

## Como funciona

Duas etapas independentes:

**1. Coleta + normalização** — cada fonte (`src/scrapers/`) baixa vagas e as
converte para o mesmo objeto `Job` (título, empresa, modalidade, senioridade,
localização, descrição, link). Da normalização em diante, a origem não importa.

**2. Qualificação** (`src/scoring.py`) — em dois passos:
- **Filtros hard** eliminam o que não serve (modalidade errada, senioridade acima
  do alvo, fora da área, remoto restrito a outro país, veto no título).
- **Score 0–100** ordena o que sobrou por aderência (skills, título, senioridade,
  modalidade, recência + bônus pelo seu background).

O resultado é uma **fila priorizada**. O envio do currículo fica com você (ver
_Roadmap_) — é onde mora o risco de ban e onde CV adaptado faz a diferença.

## Estrutura

```
job-radar/
├── main.py               # CLI
├── perfil.yaml           # SEU alvo (edite aqui)
├── config.yaml           # pesos do score e cortes
├── src/
│   ├── models.py         # Job, Perfil, enums
│   ├── normalize.py      # texto -> modalidade/senioridade/skills/datas
│   ├── scoring.py        # filtros hard + score (o coração)
│   ├── pipeline.py       # coleta -> dedupe -> qualifica -> ranqueia
│   ├── storage.py        # dedupe + export JSON/CSV
│   └── scrapers/         # fixture, remotive, gupy, linkedin
├── data/fixtures/        # dataset offline p/ testar sem rede
└── tests/                # suíte do motor + pipeline
```

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

```bash
python main.py                                   # fixture offline (não precisa de rede)
python main.py --fontes remotive --query python  # fonte real remota
python main.py --fontes gupy remotive --query "analista de dados" --limit 40
python main.py --verbose                         # mostra também as eliminadas e o motivo
```

Gera `saida/fila.json` e `saida/fila.csv`. Exemplo de saída:

```
 1. [ 83.5] Estágio em Dados — DataLab
      remoto · estagio · Remoto - Brasil
      skills: etl, git, pandas, postgresql, python, sql
      ✓ casa com seu background
 4. [ 57.3] Desenvolvedor Python Júnior — SoftX
      ⚠ júnior-fake? exige 3+ ano(s) de experiência
```

## Calibrar (sem mexer no código)

**`perfil.yaml`** — seu alvo:
- `titulos_alvo`, `skills`, `skills_obrigatorias` (ausência derruba o score, não elimina)
- `senioridades_aceitas`: `estagio`, `trainee`, `junior` (Pleno/Sênior é cortado)
- `modalidades_aceitas`: `remoto` / `hibrido` / `presencial`
- `aceita_remoto_global`: `false` = só remoto Brasil
- `keywords_bonus`: dá bônus de score (ex.: `fintech`, `contábil` — seu diferencial)
- `keywords_veto`: elimina se aparecer no título

**`config.yaml`** — pesos do score (somam ~1.0), `fuzzy_threshold` e
`score_minimo_fila` (corte pra entrar na fila).

## Fontes

| Fonte | Status | Observação |
|-------|--------|------------|
| `fixture` | ✅ offline | dataset local, sempre funciona (dev/testes) |
| `remotive` | ✅ funcional | API pública JSON, sem token — referência com dados reais |
| `gupy` | ⚠ validar | endpoint público do portal, não documentado; campos resolvidos de forma defensiva — confirme na sua máquina |
| `linkedin` | ⛔ desativado | **ToS proíbe scraping + anti-bot agressivo.** Prefira coletar manual e colar numa fixture |

### Adicionar uma fonte

1. Crie `src/scrapers/minhafonte.py` com uma classe que herda `BaseScraper` e
   implementa `fetch()`, devolvendo `Job` via `build_job(...)`.
2. Registre em `src/scrapers/__init__.py` no `REGISTRY`.
3. `python main.py --fontes minhafonte`.

## Testes

```bash
python -m pytest tests/ -v      # ou: python tests/test_scoring.py
```

Cobrem: vaga ideal pontua alto, presencial/sênior/fora-da-área/geo são eliminadas,
júnior-fake vira flag (não corte), skill obrigatória ausente penaliza, ranqueamento
por aderência e pipeline end-to-end na fixture.

## Roadmap

- **Fase 2 — camada de aplicação (semi-auto):** para cada vaga da fila, adaptar o
  CV às palavras-chave do anúncio e pré-preencher o formulário, com você dando o
  clique final. É o passo que converte, sem queimar conta.
- Persistir histórico (SQLite) pra não repontuar o que já viu.
- Mais fontes BR (Programathor, Trampos, Remotar).
- Notificação diária (agendar `main.py` e mandar a fila nova por e-mail/Telegram).
```
