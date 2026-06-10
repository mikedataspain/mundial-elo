"""
scraper.py
Extrae los Elos de las 48 selecciones del Mundial 2026 desde eloratings.net.

Estructura real de la página (SlickGrid):
  - Selector de equipos: .team-cell
  - Selector de ratings:  .rating-cell  (col 0=Rank, col 2=Elo actual, col 4=Elo medio…)
  - El Elo actual es el primer .rating-cell cuyo valor está en rango 1300-2300
  - La página usa rendering virtual: hay que hacer scroll en .slick-viewport
"""

import asyncio
import logging
import re
from datetime import date
from typing import Optional

from equivalencias import a_castellano, es_equipo_mundial, EQUIPOS_MUNDIAL_48
from config import URL_ELO, PLAYWRIGHT_TIMEOUT_MS, PLAYWRIGHT_HEADLESS

logger = logging.getLogger(__name__)


async def _extraer_elos_playwright() -> tuple[dict[str, float], str]:
    """
    Abre eloratings.net con Playwright y extrae los Elos mediante
    los selectores correctos (.team-cell / .rating-cell de SlickGrid).
    Hace scroll en .slick-viewport para cargar todos los equipos del Mundial.
    """
    from playwright.async_api import async_playwright

    elos_raw: dict[str, float] = {}      # nombre inglés → Elo
    fecha_rating = date.today().isoformat()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=PLAYWRIGHT_HEADLESS)
        page = await browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )

        logger.info(f"Navegando a {URL_ELO} …")
        await page.goto(URL_ELO, timeout=PLAYWRIGHT_TIMEOUT_MS,
                        wait_until="domcontentloaded")

        # Esperar el primer .team-cell (SlickGrid, no <table>)
        logger.info("Esperando .team-cell …")
        await page.wait_for_selector(".team-cell", timeout=25_000)
        await page.wait_for_timeout(1_500)   # margen extra para que el grid acabe de pintar

        # Extraer fecha de los ratings del encabezado de la página
        header_txt = await page.evaluate(
            "() => document.body.innerText.split('\\n').slice(0, 15).join(' ')"
        )
        m = re.search(
            r'(January|February|March|April|May|June|July|'
            r'August|September|October|November|December)'
            r'\s+\d{1,2}\s+\d{4}',
            header_txt
        )
        if m:
            fecha_rating = m.group(0)
            logger.info(f"Fecha de ratings detectada: {fecha_rating}")

        # ----------------------------------------------------------------
        # Scroll progresivo en .slick-viewport para cargar todos los equipos.
        # SlickGrid es un grid virtual: solo renderiza las filas visibles.
        # ----------------------------------------------------------------
        JS_EXTRAER_FILAS = """
            () => {
                const resultados = [];
                document.querySelectorAll('.slick-row').forEach(row => {
                    const teamCell = row.querySelector('.team-cell');
                    if (!teamCell) return;
                    const nombre = teamCell.innerText.trim();
                    if (!nombre) return;

                    // El Elo actual es el primer .rating-cell con valor en rango Elo (1300-2300).
                    // Los valores de Rank (<= 230) y los cambios (+/-nn) quedan excluidos.
                    const ratingCells = Array.from(row.querySelectorAll('.rating-cell'));
                    let elo = null;
                    for (const cell of ratingCells) {
                        const v = parseInt(cell.innerText.trim(), 10);
                        if (v >= 1300 && v <= 2300) { elo = v; break; }
                    }
                    if (elo !== null) resultados.push([nombre, elo]);
                });
                return resultados;
            }
        """

        scroll_pos   = 0
        scroll_step  = 400
        sin_nuevos   = 0
        max_sin_nuevos = 4   # parar si 4 scrolls seguidos no añaden nada

        while sin_nuevos < max_sin_nuevos:
            # Scroll del viewport interno del grid
            await page.evaluate(f"""
                () => {{
                    const vp = document.querySelector('.slick-viewport');
                    if (vp) vp.scrollTop = {scroll_pos};
                    else    window.scrollTo(0, {scroll_pos});
                }}
            """)
            await page.wait_for_timeout(200)

            filas = await page.evaluate(JS_EXTRAER_FILAS)
            antes = len(elos_raw)
            for nombre_en, elo_val in filas:
                if nombre_en and elo_val:
                    elos_raw[nombre_en] = float(elo_val)

            if len(elos_raw) == antes:
                sin_nuevos += 1
            else:
                sin_nuevos = 0
                logger.debug(f"  scroll {scroll_pos}px → {len(elos_raw)} equipos acumulados")

            scroll_pos += scroll_step

            # Salida anticipada si ya tenemos las 48 selecciones del Mundial
            ya_encontrados = sum(
                1 for n in elos_raw if es_equipo_mundial(a_castellano(n))
            )
            if ya_encontrados >= 48:
                logger.info("Todas las 48 selecciones del Mundial encontradas. "
                            "Scroll detenido.")
                break

        await browser.close()

    # ----------------------------------------------------------------
    # Mapeo inglés → castellano y filtro Mundial
    # ----------------------------------------------------------------
    elos: dict[str, float] = {}
    nombres_no_mapeados: list[str] = []

    for nombre_en, elo_val in elos_raw.items():
        nombre_es = a_castellano(nombre_en)
        if es_equipo_mundial(nombre_es):
            elos[nombre_es] = elo_val
        # Solo registrar no-mapeados si son nombres de equipos reales (no encabezados)
        elif nombre_en and len(nombre_en) > 1 and not nombre_en[0].isdigit():
            nombres_no_mapeados.append(nombre_en)

    ausentes = [eq for eq in EQUIPOS_MUNDIAL_48 if eq not in elos]
    if ausentes:
        logger.warning(
            f"Equipos del Mundial sin Elo extraído ({len(ausentes)}): "
            f"{', '.join(ausentes)}"
        )
        logger.warning(
            "Revisa equivalencias.py para añadir el mapeo de estos nombres. "
            "Nombre exacto en eloratings.net → buscar en debug_elo_text.txt."
        )

    logger.info(
        f"Elos extraídos: {len(elos)}/{len(EQUIPOS_MUNDIAL_48)} equipos del Mundial "
        f"(total en grid: {len(elos_raw)})"
    )
    return elos, fecha_rating


def obtener_elos_con_fallback(
    elos_anteriores: Optional[dict] = None,
) -> tuple[dict, str]:
    """
    Punto de entrada síncrono.
    Intenta extraer de eloratings.net; si falla, usa el caché anterior.
    """
    try:
        elos, fecha = asyncio.run(_extraer_elos_playwright())
        if len([e for e in elos if e in EQUIPOS_MUNDIAL_48]) >= 20:
            return elos, fecha
        logger.warning(
            f"Pocos equipos extraídos ({len(elos)}). "
            "Puede que la página haya tardado más de lo esperado."
        )
    except Exception as exc:
        logger.error(f"Error en scraping: {exc}")
        elos, fecha = {}, date.today().isoformat()

    if elos_anteriores:
        logger.error(
            "Extracción fallida. Usando Elos del día anterior. "
            "Los outputs NO se sobrescribirán (la validación lo bloqueará)."
        )
        return elos_anteriores, date.today().isoformat()

    return elos, date.today().isoformat()
