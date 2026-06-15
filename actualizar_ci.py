"""
actualizar_ci.py
Pipeline para GitHub Actions: scraping → Monte Carlo → data.csv
Sin Google Sheets, sin PNGs, sin Google Docs.
"""

import logging
import shutil
import sys
import time
from datetime import date
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("actualizar_ci")

from config import CSV_PRONOSTICADOR, JSON_CACHE_PROBS, N_SIMULACIONES
from equivalencias import GRUPOS, EQUIPOS_MUNDIAL_48
from fixtures import get_calendario
from modelo import calcular_probabilidades_fase_grupos, simular_torneo_completo
from resultados import obtener_resultados_jugados
from scraper import obtener_elos_con_fallback
from validacion import (
    cargar_elos_anteriores,
    guardar_elos_cache,
    guardar_probs_cache,
    validar_todo,
    ValidationError,
)


def main():
    inicio = time.time()
    hoy = date.today().isoformat()
    logger.info(f"INICIO PIPELINE CI — {hoy}")

    # 1. Scraping
    elos_anteriores = cargar_elos_anteriores()
    logger.info("Extrayendo Elos de eloratings.net…")
    try:
        elos, fecha_ratings = obtener_elos_con_fallback(elos_anteriores)
    except Exception as exc:
        logger.error(f"Error en scraping: {exc}")
        sys.exit(1)

    for eq in EQUIPOS_MUNDIAL_48:
        if eq not in elos:
            elos[eq] = 1500.0
            logger.warning(f"Elo no encontrado para '{eq}', usando 1500.")

    logger.info(f"Equipos extraídos: {len([e for e in EQUIPOS_MUNDIAL_48 if e in elos])}/48")

    # 2. Validaciones
    try:
        validar_todo(elos)
    except ValidationError as ve:
        logger.error(f"VALIDACIÓN FALLIDA — pipeline abortado: {ve}")
        sys.exit(1)

    # 3. Monte Carlo
    logger.info(f"Simulando {N_SIMULACIONES:,} iteraciones de Monte Carlo…")
    t0 = time.time()
    calendario = get_calendario(GRUPOS)
    calcular_probabilidades_fase_grupos(calendario, elos)
    resultados_reales = obtener_resultados_jugados(calendario)
    df = simular_torneo_completo(GRUPOS, elos, n_sims=N_SIMULACIONES,
                                 resultados_reales=resultados_reales)
    logger.info(f"Monte Carlo completado en {time.time() - t0:.1f}s.")

    # 4. Exportar CSV y copiar a data.csv
    cols = ["Selección", "Grupos%", "1/32%", "1/16%", "Cuartos%", "Semis%", "Campeón%"]
    cols_out = [c for c in cols if c in df.columns]
    df[cols_out].to_csv(CSV_PRONOSTICADOR, index=False, encoding="utf-8-sig")

    repo_root = Path(__file__).parent
    shutil.copy(CSV_PRONOSTICADOR, repo_root / "data.csv")
    logger.info(f"data.csv actualizado → {repo_root / 'data.csv'}")

    # 5. Guardar caché para la siguiente ejecución
    guardar_elos_cache(elos, fecha=fecha_ratings)
    probs_hoy = {
        row["Selección"]: {col: row[col] for col in cols_out if col != "Selección"}
        for _, row in df.iterrows()
    }
    guardar_probs_cache({"probs": probs_hoy, "elos": elos}, JSON_CACHE_PROBS, fecha=hoy)

    elapsed = time.time() - inicio
    top3 = df.nlargest(3, "Campeón%")[["Selección", "Campeón%"]].to_string(index=False)
    logger.info(f"COMPLETADO en {elapsed:.1f}s — Top 3:\n{top3}")


if __name__ == "__main__":
    main()
