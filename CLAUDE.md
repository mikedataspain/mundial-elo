# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**mundial-elo** is a World Cup 2026 Elo-based probability predictor. It runs as a daily GitHub Actions job that scrapes live Elo ratings, runs 100,000 Monte Carlo simulations, and publishes the results as `data.csv` (consumed by `index.html`, a static dashboard). The codebase is Python 3.11 with no web framework — all modules live flat at the repo root.

## Commands

**Install dependencies:**
```bash
pip install -r requirements_ci.txt
playwright install chromium --with-deps
```

**Run the full pipeline locally:**
```bash
python actualizar_ci.py
```

**Run a single module in isolation** (useful for debugging individual steps):
```bash
python -c "from scraper import obtener_elos_con_fallback; import asyncio; print(asyncio.run(obtener_elos_con_fallback({})))"
python -c "from modelo import simular_torneo_completo; from equivalencias import GRUPOS; print(simular_torneo_completo(GRUPOS, {}, n_sims=1000))"
```

There is no test suite or linter configured.

## Architecture

The pipeline has four sequential stages, orchestrated by `actualizar_ci.py`:

```
scraper.py → validacion.py → modelo.py → data.csv
```

1. **`scraper.py`** — Async Playwright scraper targeting `eloratings.net`. Navigates a SlickGrid table (`.slick-viewport`, `.team-cell`, `.rating-cell` selectors), extracts team names + Elo values for all 48 World Cup teams. Falls back to `.cache/elos_anterior.json` on failure.

2. **`validacion.py`** — Validates the scraped Elos before simulation: requires ≥40 of 48 teams (`MIN_EQUIPOS_REQUERIDOS`), Elo values in [1200, 2300]. Raises `ValidationError` to abort the pipeline. Also writes/reads the JSON caches.

3. **`modelo.py`** — Core math engine. Group stage is fully vectorized with NumPy (100k × 6 matches × 12 groups simultaneously). Knockout bracket uses hardcoded structures (`CRUCES_R32`, `BRACKET_R16`, etc.). Draw probability uses piecewise linear interpolation over `DRAW_CALIBRATION` (no draws in knockout). Output is a DataFrame with columns `Selección, Grupos%, 1/32%, 1/16%, Cuartos%, Semis%, Campeón%`.

4. **`equivalencias.py`** — The translation layer between eloratings.net English names and Spanish display names. Contains `EQUIVALENCIAS_EN_ES` (214 entries), the authoritative 48-team list `EQUIPOS_MUNDIAL_48`, and group assignments `GRUPOS` (dict of group letter → list of Spanish team names). **All internal logic uses Spanish names as the canonical identifier.**

5. **`fixtures.py`** — Provides `get_calendario()`, which returns the 72 group-stage matches as a list of dicts with date, teams, and stadium. Dates are hardcoded for June 11–27, 2026.

6. **`config.py`** — Single source of truth for all paths, model parameters, scraping config, and Google Sheets IDs. Edit here to change `N_SIMULACIONES`, Playwright timeout, or output directories.

## Key Conventions

- **Spanish names are canonical.** `EQUIPOS_MUNDIAL_48` and `GRUPOS` in `equivalencias.py` use Spanish. The scraper translates English → Spanish immediately via `a_castellano()`. Never use English team names as dict keys inside the simulation.

- **Missing teams default to Elo 1500.** If a team from `EQUIPOS_MUNDIAL_48` is not scraped, `actualizar_ci.py` assigns 1500.0 with a warning rather than aborting.

- **CI skips if already run today.** The workflow checks `git log` on `data.csv` against today's Madrid date before running anything.

- **Output paths:**
  - `data.csv` — repo root, committed by CI, read by `index.html`
  - `Mundial/mundial2026_tabla_rondas.csv` — same data, intermediate path (`CSV_PRONOSTICADOR`)
  - `.cache/elos_anterior.json` — persisted between CI runs as scraper fallback
  - `logs/` and `Mundial/` are gitignored

- **Google Sheets integration** (`SPREADSHEET_ID`, `DOCUMENT_ID` in `config.py`) is not part of the CI pipeline (`actualizar_ci.py` explicitly skips it). Those constants exist for a separate local workflow.

- **`credentials/service_account.json`** is required only for Google Sheets/Docs export, not for the CI pipeline.
