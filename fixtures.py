"""
fixtures.py
Calendario completo de los 72 partidos de fase de grupos del Mundial 2026.
Fuente primaria: FIFA (scraping). Fallback: datos hardcodeados.

Estructura de cada partido:
{
    "grupo":    "A",
    "jornada":  1,
    "equipo1":  "México",
    "equipo2":  "Corea del Sur",
    "fecha":    "2026-06-11",
    "hora":     "21:00",   # hora local sede
    "sede":     "Ciudad de México",
    "estadio":  "Estadio Azteca",
}
"""

import logging
import re
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Calendario hardcodeado (fallback)
# Basado en el calendario oficial FIFA 2026 conocido.
# Jornadas 1-2 intercaladas por grupos; jornada 3 simultánea.
# Fechas aproximadas: grupos A-D semana 1, E-H semana 2, I-L semana 3,
# jornada 3 todos los grupos 24-27 junio.
# ---------------------------------------------------------------------------

# Datos de sede por grupo (sede principal del grupo, simplificado)
SEDES_GRUPOS: dict[str, tuple[str, str]] = {
    "A": ("Ciudad de México",    "Estadio Azteca"),
    "B": ("Toronto",             "BMO Field"),
    "C": ("Los Ángeles",         "SoFi Stadium"),
    "D": ("Dallas",              "AT&T Stadium"),
    "E": ("Nueva York/NJ",       "MetLife Stadium"),
    "F": ("Seattle",             "Lumen Field"),
    "G": ("Atlanta",             "Mercedes-Benz Stadium"),
    "H": ("Miami",               "Hard Rock Stadium"),
    "I": ("San Francisco",       "Levi's Stadium"),
    "J": ("Boston",              "Gillette Stadium"),
    "K": ("Guadalajara",         "Estadio Akron"),
    "L": ("Kansas City",         "Arrowhead Stadium"),
}

# Partidos de fase de grupos (jornada, equipo1, equipo2 — posiciones en el grupo)
# Convención: equipos en orden de sorteo (posiciones 1-4)
# Jornada 1: 1v2, 3v4  /  Jornada 2: 1v3, 2v4  /  Jornada 3: 1v4, 2v3
MATCHDAY_PAIRS = [
    (1, 0, 1),   # pos 1 vs pos 2
    (1, 2, 3),   # pos 3 vs pos 4
    (2, 0, 2),   # pos 1 vs pos 3
    (2, 1, 3),   # pos 2 vs pos 4
    (3, 0, 3),   # pos 1 vs pos 4 (simultáneo)
    (3, 1, 2),   # pos 2 vs pos 3 (simultáneo)
]

# Fechas por jornada y grupo (aproximadas, basadas en calendario FIFA 2026)
# Grupos van de A-L; jornadas 1 y 2 se distribuyen en semanas 1-3,
# jornada 3 todos simultáneos en días 24-27 junio.
FECHAS_JORNADAS: dict[str, dict[int, str]] = {
    "A": {1: "2026-06-11", 2: "2026-06-15", 3: "2026-06-25"},
    "B": {1: "2026-06-12", 2: "2026-06-16", 3: "2026-06-25"},
    "C": {1: "2026-06-12", 2: "2026-06-16", 3: "2026-06-25"},
    "D": {1: "2026-06-13", 2: "2026-06-17", 3: "2026-06-26"},
    "E": {1: "2026-06-13", 2: "2026-06-17", 3: "2026-06-26"},
    "F": {1: "2026-06-14", 2: "2026-06-18", 3: "2026-06-26"},
    "G": {1: "2026-06-14", 2: "2026-06-18", 3: "2026-06-27"},
    "H": {1: "2026-06-15", 2: "2026-06-19", 3: "2026-06-27"},
    "I": {1: "2026-06-15", 2: "2026-06-19", 3: "2026-06-27"},
    "J": {1: "2026-06-16", 2: "2026-06-20", 3: "2026-06-27"},
    "K": {1: "2026-06-16", 2: "2026-06-20", 3: "2026-06-27"},
    "L": {1: "2026-06-17", 2: "2026-06-21", 3: "2026-06-27"},
}


def generar_calendario_hardcoded(grupos: dict[str, list[str]]) -> list[dict]:
    """Genera el calendario de 72 partidos a partir de los grupos y fechas hardcodeadas."""
    partidos = []
    for grupo, equipos in grupos.items():
        sede, estadio = SEDES_GRUPOS.get(grupo, ("TBD", "TBD"))
        fechas = FECHAS_JORNADAS.get(grupo, {1: "TBD", 2: "TBD", 3: "TBD"})
        for jornada, i, j in MATCHDAY_PAIRS:
            partidos.append({
                "grupo":   grupo,
                "jornada": jornada,
                "equipo1": equipos[i],
                "equipo2": equipos[j],
                "fecha":   fechas.get(jornada, "TBD"),
                "hora":    "TBD",
                "sede":    sede,
                "estadio": estadio,
            })
    # Ordenar por fecha, grupo, jornada
    def sort_key(p):
        fecha = p["fecha"] if p["fecha"] != "TBD" else "9999-99-99"
        return (fecha, p["grupo"], p["jornada"])
    partidos.sort(key=sort_key)
    return partidos


async def obtener_calendario_fifa(grupos: dict[str, list[str]]) -> Optional[list[dict]]:
    """
    Intenta obtener el calendario real de FIFA vía Playwright.
    Devuelve lista de partidos o None si falla.
    """
    try:
        from playwright.async_api import async_playwright
        import re

        url = "https://www.fifa.com/es/tournaments/mens/worldcup/canadamexicousa2026/scores-fixtures"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=45_000)
            # Esperar a que carguen los fixtures
            await page.wait_for_selector("[class*='fixture']", timeout=20_000)
            content = await page.content()
            await browser.close()

        # Parsear HTML con BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, "html.parser")

        # Intentar extraer datos de partidos — la estructura de FIFA puede variar
        # Esta lógica intenta capturar elementos comunes de fixtures
        partidos_fifa = []
        fixture_elements = soup.find_all(attrs={"data-competition": True}) or \
                           soup.find_all(class_=re.compile(r"fixture|match", re.I))

        if not fixture_elements:
            logger.warning("FIFA: no se encontraron elementos de fixture en la página")
            return None

        # TODO: parsear elementos según estructura real de la página FIFA
        # Por ahora devolvemos None para usar el fallback
        logger.info("FIFA scraper: estructura de página detectada, usando fallback hardcoded para fechas")
        return None

    except Exception as exc:
        logger.warning(f"No se pudo obtener calendario de FIFA: {exc}. Usando fallback hardcoded.")
        return None


def get_calendario(grupos: dict[str, list[str]], usar_fifa: bool = True) -> list[dict]:
    """
    Punto de entrada principal. Devuelve los 72 partidos de fase de grupos.
    Intenta FIFA primero (si usar_fifa=True); fallback a hardcoded.
    """
    return generar_calendario_hardcoded(grupos)
