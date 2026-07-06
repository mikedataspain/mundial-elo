"""
resultados.py
Obtiene resultados reales de partidos jugados del Mundial 2026.
Fuente: ESPN API pública (sin autenticación, sin clave).
Fallback: si la API no responde, devuelve dict vacío y el modelo simula todo.
"""

import json
import logging
import urllib.request
from datetime import date
from typing import Optional

from equivalencias import EQUIVALENCIAS_EN_ES

logger = logging.getLogger(__name__)

# Nombres ESPN que difieren ligeramente de los de eloratings
_ESPN_EXTRA: dict[str, str] = {
    "United States":           "EE.UU.",
    "USA":                     "EE.UU.",
    "Ivory Coast":             "Costa de Marfil",
    "DR Congo":                "RD Congo",
    "Republic of Ireland":     "Irlanda",
    "Curaçao":                 "Curazao",
    "Bosnia and Herzegovina":  "Bosnia-Herz.",
}


def _espn_a_castellano(nombre: str) -> str:
    return _ESPN_EXTRA.get(nombre) or EQUIVALENCIAS_EN_ES.get(nombre) or nombre


def _fetch_dia_espn(fecha_yyyymmdd: str) -> list[tuple[str, str, int, int, int, int]]:
    """
    Obtiene los partidos terminados de un día desde la ESPN public API.
    Devuelve lista de (eq1_es, eq2_es, pts_eq1, pts_eq2, goles_eq1, goles_eq2).
    """
    url = (
        "https://site.api.espn.com/apis/site/v2/sports/soccer"
        f"/fifa.world/scoreboard?dates={fecha_yyyymmdd}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:
        logger.warning("ESPN API no disponible para %s: %s", fecha_yyyymmdd, exc)
        return []

    partidos = []
    for event in data.get("events", []):
        estado = event.get("status", {}).get("type", {}).get("state", "")
        if estado != "post":          # solo partidos terminados
            continue
        comps = event.get("competitions", [{}])[0].get("competitors", [])
        if len(comps) != 2:
            continue

        teams: dict[str, int] = {}
        for c in comps:
            nombre_espn = c.get("team", {}).get("displayName", "")
            score = int(c.get("score") or 0)
            teams[nombre_espn] = score

        if len(teams) != 2:
            continue

        nombres = list(teams)
        g1, g2 = teams[nombres[0]], teams[nombres[1]]

        if g1 > g2:
            pts1, pts2 = 3, 0
        elif g1 == g2:
            pts1, pts2 = 1, 1
        else:
            pts1, pts2 = 0, 3

        eq1 = _espn_a_castellano(nombres[0])
        eq2 = _espn_a_castellano(nombres[1])
        logger.debug("ESPN: %s %d-%d %s → pts %d/%d", eq1, g1, g2, eq2, pts1, pts2)
        partidos.append((eq1, eq2, pts1, pts2, g1, g2))

    return partidos


def _fetch_dia_espn_playoff(fecha_yyyymmdd: str) -> list[tuple[str, str, str]]:
    """
    Obtiene partidos eliminatorios terminados de un día.
    Devuelve lista de (eq1_es, eq2_es, nombre_ganador_es).
    Usa el campo 'winner' de ESPN (los partidos de penaltis terminan
    empatados en el marcador, así que no se puede comparar goles).
    """
    url = (
        "https://site.api.espn.com/apis/site/v2/sports/soccer"
        f"/fifa.world/scoreboard?dates={fecha_yyyymmdd}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:
        logger.warning("ESPN API no disponible para %s: %s", fecha_yyyymmdd, exc)
        return []

    partidos = []
    for event in data.get("events", []):
        if event.get("status", {}).get("type", {}).get("state", "") != "post":
            continue
        comps = event.get("competitions", [{}])[0].get("competitors", [])
        if len(comps) != 2:
            continue

        ganador_nombre = None
        nombres = []
        for c in comps:
            nombre_es = _espn_a_castellano(c.get("team", {}).get("displayName", ""))
            nombres.append(nombre_es)
            if c.get("winner"):
                ganador_nombre = nombre_es

        if len(nombres) == 2 and ganador_nombre:
            partidos.append((nombres[0], nombres[1], ganador_nombre))
            logger.debug("ESPN KO: %s vs %s → ganador %s", nombres[0], nombres[1], ganador_nombre)

    return partidos


# Fechas oficiales de cada ronda del Mundial 2026
_PLAYOFF_FECHAS: list[tuple] = [
    ("R32", date(2026, 6, 28), date(2026, 7, 3)),
    ("R16", date(2026, 7, 4),  date(2026, 7, 8)),
    ("QF",  date(2026, 7, 10), date(2026, 7, 11)),
    ("SF",  date(2026, 7, 14), date(2026, 7, 15)),
    ("F",   date(2026, 7, 19), date(2026, 7, 19)),
]


def _ronda_por_fecha(fecha: date) -> str:
    for nombre, inicio, fin in _PLAYOFF_FECHAS:
        if inicio <= fecha <= fin:
            return nombre
    return "R32"


def obtener_resultados_playoff(
    fecha_hoy: Optional[date] = None,
) -> dict:
    """
    Obtiene resultados ya jugados de la fase eliminatoria (R32 en adelante).
    Retorna {frozenset({eq1, eq2}): {"ganador": nombre, "ronda": "R32"|"R16"|"QF"|"SF"|"F"}}
    """
    if fecha_hoy is None:
        fecha_hoy = date.today()

    from datetime import date as _date, timedelta
    inicio_playoff = _date(2026, 6, 28)

    if fecha_hoy < inicio_playoff:
        return {}

    resultados: dict = {}
    dia = inicio_playoff
    while dia <= fecha_hoy:
        ronda = _ronda_por_fecha(dia)
        for eq1, eq2, ganador in _fetch_dia_espn_playoff(dia.strftime("%Y%m%d")):
            resultados[frozenset({eq1, eq2})] = {"ganador": ganador, "ronda": ronda}
        dia += timedelta(days=1)

    if resultados:
        logger.info("Resultados playoff: %d partidos obtenidos de ESPN.", len(resultados))
    return resultados


def obtener_resultados_jugados(
    calendario: list[dict],
    fecha_hoy: Optional[date] = None,
) -> dict:
    """
    Para cada partido del calendario con fecha < hoy, obtiene el resultado real.

    Retorna:
        {frozenset({eq1, eq2}): {eq1: pts_eq1, eq2: pts_eq2, "goles": {eq1: g1, eq2: g2}}}

    Si ESPN no devuelve resultado para un partido ya jugado, ese partido
    se omite del dict y el modelo lo simulará normalmente (fallback seguro).
    """
    if fecha_hoy is None:
        fecha_hoy = date.today()

    fechas_pasadas = sorted(set(
        p["fecha"] for p in calendario
        if p.get("fecha", "9999-99-99") < fecha_hoy.isoformat()
    ))

    if not fechas_pasadas:
        logger.info("Sin partidos jugados antes de hoy — simulación completa.")
        return {}

    resultados: dict = {}
    for fecha_str in fechas_pasadas:
        dia = _fetch_dia_espn(fecha_str.replace("-", ""))
        for eq1, eq2, pts1, pts2, g1, g2 in dia:
            key = frozenset({eq1, eq2})
            resultados[key] = {eq1: pts1, eq2: pts2, "goles": {eq1: g1, eq2: g2}}

    n_esperados = sum(
        1 for p in calendario
        if p.get("fecha", "9999-99-99") < fecha_hoy.isoformat()
    )
    logger.info(
        "Resultados reales: %d/%d partidos jugados obtenidos de ESPN.",
        len(resultados), n_esperados,
    )
    return resultados
