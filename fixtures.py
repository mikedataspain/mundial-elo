"""
fixtures.py
Calendario completo de los 72 partidos de fase de grupos del Mundial 2026.
Fuente: ESPN / FIFA oficial — verificado 17/06/2026.

Estructura de cada partido:
{
    "grupo":    "A",
    "jornada":  1,
    "equipo1":  "México",
    "equipo2":  "Corea del Sur",
    "fecha":    "2026-06-11",
    "hora":     "TBD",
    "sede":     "Ciudad de México",
    "estadio":  "Estadio Azteca",
}
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sede por partido (clave: frozenset de los dos equipos)
# 72 partidos → 72 entradas. Fuente: ESPN / FIFA 2026 — verificado 17/06/2026.
# ---------------------------------------------------------------------------
SEDES_PARTIDOS: dict[frozenset, tuple[str, str]] = {
    # ─── GRUPO A  (México · Corea del Sur · Rep. Checa · Sudáfrica) ─────────
    frozenset({"México",         "Sudáfrica"}):      ("Ciudad de México", "Estadio Azteca"),       # Jun 11
    frozenset({"Corea del Sur",  "Rep. Checa"}):     ("Guadalajara",      "Estadio Akron"),        # Jun 11
    frozenset({"Rep. Checa",     "Sudáfrica"}):      ("Atlanta",          "Mercedes-Benz Stadium"),# Jun 18
    frozenset({"México",         "Corea del Sur"}):  ("Guadalajara",      "Estadio Akron"),        # Jun 18
    frozenset({"Rep. Checa",     "México"}):         ("Ciudad de México", "Estadio Azteca"),       # Jun 24
    frozenset({"Sudáfrica",      "Corea del Sur"}):  ("Monterrey",        "Estadio BBVA"),         # Jun 24

    # ─── GRUPO B  (Canadá · Bosnia-Herz. · Qatar · Suiza) ──────────────────
    frozenset({"Canadá",         "Bosnia-Herz."}):   ("Toronto",          "BMO Field"),            # Jun 12
    frozenset({"Qatar",          "Suiza"}):          ("San Francisco",    "Levi's Stadium"),       # Jun 13
    frozenset({"Suiza",          "Bosnia-Herz."}):   ("Los Ángeles",      "SoFi Stadium"),         # Jun 18
    frozenset({"Canadá",         "Qatar"}):          ("Vancouver",        "BC Place"),             # Jun 18
    frozenset({"Suiza",          "Canadá"}):         ("Vancouver",        "BC Place"),             # Jun 24
    frozenset({"Bosnia-Herz.",   "Qatar"}):          ("Seattle",          "Lumen Field"),          # Jun 24

    # ─── GRUPO C  (Brasil · Marruecos · Haití · Escocia) ───────────────────
    frozenset({"Brasil",         "Marruecos"}):      ("Nueva York/NJ",    "MetLife Stadium"),      # Jun 13
    frozenset({"Haití",          "Escocia"}):        ("Boston",           "Gillette Stadium"),     # Jun 13
    frozenset({"Escocia",        "Marruecos"}):      ("Boston",           "Gillette Stadium"),     # Jun 19
    frozenset({"Brasil",         "Haití"}):          ("Philadelphia",     "Lincoln Financial Field"), # Jun 19
    frozenset({"Escocia",        "Brasil"}):         ("Miami",            "Hard Rock Stadium"),    # Jun 24
    frozenset({"Marruecos",      "Haití"}):          ("Atlanta",          "Mercedes-Benz Stadium"),# Jun 24

    # ─── GRUPO D  (EE.UU. · Paraguay · Australia · Turquía) ─────────────────
    frozenset({"EE.UU.",         "Paraguay"}):       ("Los Ángeles",      "SoFi Stadium"),         # Jun 12
    frozenset({"Australia",      "Turquía"}):        ("Vancouver",        "BC Place"),             # Jun 13
    frozenset({"EE.UU.",         "Australia"}):      ("Seattle",          "Lumen Field"),          # Jun 19
    frozenset({"Turquía",        "Paraguay"}):       ("San Francisco",    "Levi's Stadium"),       # Jun 19
    frozenset({"Turquía",        "EE.UU."}):         ("Los Ángeles",      "SoFi Stadium"),         # Jun 25
    frozenset({"Paraguay",       "Australia"}):      ("San Francisco",    "Levi's Stadium"),       # Jun 25

    # ─── GRUPO E  (Alemania · Ecuador · Costa de Marfil · Curazao) ──────────
    frozenset({"Alemania",       "Curazao"}):        ("Houston",          "NRG Stadium"),          # Jun 14
    frozenset({"Costa de Marfil","Ecuador"}):        ("Philadelphia",     "Lincoln Financial Field"), # Jun 14
    frozenset({"Alemania",       "Costa de Marfil"}):("Toronto",          "BMO Field"),            # Jun 20
    frozenset({"Ecuador",        "Curazao"}):        ("Kansas City",      "Arrowhead Stadium"),    # Jun 20
    frozenset({"Curazao",        "Costa de Marfil"}):("Philadelphia",     "Lincoln Financial Field"), # Jun 25
    frozenset({"Ecuador",        "Alemania"}):       ("Nueva York/NJ",    "MetLife Stadium"),      # Jun 25

    # ─── GRUPO F  (Países Bajos · Japón · Suecia · Túnez) ──────────────────
    frozenset({"Países Bajos",   "Japón"}):          ("Dallas",           "AT&T Stadium"),         # Jun 14
    frozenset({"Suecia",         "Túnez"}):          ("Monterrey",        "Estadio BBVA"),         # Jun 14
    frozenset({"Países Bajos",   "Suecia"}):         ("Houston",          "NRG Stadium"),          # Jun 20
    frozenset({"Japón",          "Túnez"}):          ("Monterrey",        "Estadio BBVA"),         # Jun 20
    frozenset({"Japón",          "Suecia"}):         ("Dallas",           "AT&T Stadium"),         # Jun 25
    frozenset({"Túnez",          "Países Bajos"}):   ("Kansas City",      "Arrowhead Stadium"),    # Jun 25

    # ─── GRUPO G  (Bélgica · Irán · Egipto · Nueva Zelanda) ────────────────
    frozenset({"Bélgica",        "Egipto"}):         ("Seattle",          "Lumen Field"),          # Jun 15
    frozenset({"Irán",           "Nueva Zelanda"}):  ("Los Ángeles",      "SoFi Stadium"),         # Jun 15
    frozenset({"Bélgica",        "Irán"}):           ("Los Ángeles",      "SoFi Stadium"),         # Jun 21
    frozenset({"Nueva Zelanda",  "Egipto"}):         ("Vancouver",        "BC Place"),             # Jun 21
    frozenset({"Egipto",         "Irán"}):           ("Seattle",          "Lumen Field"),          # Jun 26
    frozenset({"Nueva Zelanda",  "Bélgica"}):        ("Vancouver",        "BC Place"),             # Jun 26

    # ─── GRUPO H  (España · Uruguay · Arabia Saudí · Cabo Verde) ────────────
    frozenset({"España",         "Cabo Verde"}):     ("Atlanta",          "Mercedes-Benz Stadium"),# Jun 15
    frozenset({"Arabia Saudí",   "Uruguay"}):        ("Miami",            "Hard Rock Stadium"),    # Jun 15
    frozenset({"España",         "Arabia Saudí"}):   ("Atlanta",          "Mercedes-Benz Stadium"),# Jun 21
    frozenset({"Uruguay",        "Cabo Verde"}):     ("Miami",            "Hard Rock Stadium"),    # Jun 21
    frozenset({"Cabo Verde",     "Arabia Saudí"}):   ("Houston",          "NRG Stadium"),          # Jun 26
    frozenset({"Uruguay",        "España"}):         ("Guadalajara",      "Estadio Akron"),        # Jun 26

    # ─── GRUPO I  (Francia · Senegal · Irak · Noruega) ──────────────────────
    frozenset({"Francia",        "Senegal"}):        ("Nueva York/NJ",    "MetLife Stadium"),      # Jun 16
    frozenset({"Irak",           "Noruega"}):        ("Boston",           "Gillette Stadium"),     # Jun 16
    frozenset({"Francia",        "Irak"}):           ("Philadelphia",     "Lincoln Financial Field"), # Jun 22
    frozenset({"Noruega",        "Senegal"}):        ("Nueva York/NJ",    "MetLife Stadium"),      # Jun 22
    frozenset({"Noruega",        "Francia"}):        ("Boston",           "Gillette Stadium"),     # Jun 26
    frozenset({"Senegal",        "Irak"}):           ("Toronto",          "BMO Field"),            # Jun 26

    # ─── GRUPO J  (Argentina · Argelia · Austria · Jordania) ────────────────
    frozenset({"Argentina",      "Argelia"}):        ("Kansas City",      "Arrowhead Stadium"),    # Jun 16
    frozenset({"Austria",        "Jordania"}):       ("San Francisco",    "Levi's Stadium"),       # Jun 16
    frozenset({"Argentina",      "Austria"}):        ("Dallas",           "AT&T Stadium"),         # Jun 22
    frozenset({"Jordania",       "Argelia"}):        ("San Francisco",    "Levi's Stadium"),       # Jun 22
    frozenset({"Argelia",        "Austria"}):        ("Kansas City",      "Arrowhead Stadium"),    # Jun 27
    frozenset({"Jordania",       "Argentina"}):      ("Dallas",           "AT&T Stadium"),         # Jun 27

    # ─── GRUPO K  (Portugal · RD Congo · Uzbekistán · Colombia) ─────────────
    frozenset({"Portugal",       "RD Congo"}):       ("Houston",          "NRG Stadium"),          # Jun 17
    frozenset({"Uzbekistán",     "Colombia"}):       ("Ciudad de México", "Estadio Azteca"),       # Jun 17
    frozenset({"Portugal",       "Uzbekistán"}):     ("Houston",          "NRG Stadium"),          # Jun 23
    frozenset({"Colombia",       "RD Congo"}):       ("Guadalajara",      "Estadio Akron"),        # Jun 23
    frozenset({"Colombia",       "Portugal"}):       ("Miami",            "Hard Rock Stadium"),    # Jun 27
    frozenset({"RD Congo",       "Uzbekistán"}):     ("Atlanta",          "Mercedes-Benz Stadium"),# Jun 27

    # ─── GRUPO L  (Inglaterra · Croacia · Ghana · Panamá) ───────────────────
    frozenset({"Inglaterra",     "Croacia"}):        ("Dallas",           "AT&T Stadium"),         # Jun 17
    frozenset({"Ghana",          "Panamá"}):         ("Toronto",          "BMO Field"),            # Jun 17
    frozenset({"Inglaterra",     "Ghana"}):          ("Boston",           "Gillette Stadium"),     # Jun 23
    frozenset({"Panamá",         "Croacia"}):        ("Toronto",          "BMO Field"),            # Jun 23
    frozenset({"Panamá",         "Inglaterra"}):     ("Nueva York/NJ",    "MetLife Stadium"),      # Jun 27
    frozenset({"Croacia",        "Ghana"}):          ("Philadelphia",     "Lincoln Financial Field"), # Jun 27
}

# ---------------------------------------------------------------------------
# Pares de partidos por jornada (posiciones dentro del grupo 0-3)
# Jornada 1: 1v2, 3v4 / Jornada 2: 1v3, 2v4 / Jornada 3: 1v4, 2v3
# ---------------------------------------------------------------------------
MATCHDAY_PAIRS = [
    (1, 0, 1),
    (1, 2, 3),
    (2, 0, 2),
    (2, 1, 3),
    (3, 0, 3),
    (3, 1, 2),
]

# ---------------------------------------------------------------------------
# Fechas por jornada y grupo (referencia; la fuente principal es FECHAS_PARTIDOS)
# Fuente: ESPN / FIFA 2026 — verificado 17/06/2026.
# ---------------------------------------------------------------------------
FECHAS_JORNADAS: dict[str, dict[int, str]] = {
    "A": {1: "2026-06-11", 2: "2026-06-18", 3: "2026-06-24"},
    "B": {1: "2026-06-12", 2: "2026-06-18", 3: "2026-06-24"},
    "C": {1: "2026-06-13", 2: "2026-06-19", 3: "2026-06-24"},
    "D": {1: "2026-06-12", 2: "2026-06-19", 3: "2026-06-25"},
    "E": {1: "2026-06-14", 2: "2026-06-20", 3: "2026-06-25"},
    "F": {1: "2026-06-14", 2: "2026-06-20", 3: "2026-06-25"},
    "G": {1: "2026-06-15", 2: "2026-06-21", 3: "2026-06-26"},
    "H": {1: "2026-06-15", 2: "2026-06-21", 3: "2026-06-26"},
    "I": {1: "2026-06-16", 2: "2026-06-22", 3: "2026-06-26"},
    "J": {1: "2026-06-16", 2: "2026-06-22", 3: "2026-06-27"},
    "K": {1: "2026-06-17", 2: "2026-06-23", 3: "2026-06-27"},
    "L": {1: "2026-06-17", 2: "2026-06-23", 3: "2026-06-27"},
}

# ---------------------------------------------------------------------------
# Fecha exacta por partido (clave: frozenset de los dos equipos)
# Fuente: ESPN / FIFA 2026 — verificado 17/06/2026.
# Nota: se usa la fecha local del estadio (no hora ET).
# ---------------------------------------------------------------------------
FECHAS_PARTIDOS: dict[frozenset, str] = {
    # ─── GRUPO A ──────────────────────────────────────────────────────────────
    frozenset({"México",         "Sudáfrica"}):      "2026-06-11",
    frozenset({"Corea del Sur",  "Rep. Checa"}):     "2026-06-11",
    frozenset({"Rep. Checa",     "Sudáfrica"}):      "2026-06-18",
    frozenset({"México",         "Corea del Sur"}):  "2026-06-18",
    frozenset({"Rep. Checa",     "México"}):         "2026-06-24",
    frozenset({"Sudáfrica",      "Corea del Sur"}):  "2026-06-24",

    # ─── GRUPO B ──────────────────────────────────────────────────────────────
    frozenset({"Canadá",         "Bosnia-Herz."}):   "2026-06-12",
    frozenset({"Qatar",          "Suiza"}):          "2026-06-13",
    frozenset({"Suiza",          "Bosnia-Herz."}):   "2026-06-18",
    frozenset({"Canadá",         "Qatar"}):          "2026-06-18",
    frozenset({"Suiza",          "Canadá"}):         "2026-06-24",
    frozenset({"Bosnia-Herz.",   "Qatar"}):          "2026-06-24",

    # ─── GRUPO C ──────────────────────────────────────────────────────────────
    frozenset({"Brasil",         "Marruecos"}):      "2026-06-13",
    frozenset({"Haití",          "Escocia"}):        "2026-06-13",
    frozenset({"Escocia",        "Marruecos"}):      "2026-06-19",
    frozenset({"Brasil",         "Haití"}):          "2026-06-19",
    frozenset({"Escocia",        "Brasil"}):         "2026-06-24",
    frozenset({"Marruecos",      "Haití"}):          "2026-06-24",

    # ─── GRUPO D ──────────────────────────────────────────────────────────────
    frozenset({"EE.UU.",         "Paraguay"}):       "2026-06-12",
    frozenset({"Australia",      "Turquía"}):        "2026-06-13",
    frozenset({"EE.UU.",         "Australia"}):      "2026-06-19",
    frozenset({"Turquía",        "Paraguay"}):       "2026-06-19",
    frozenset({"Turquía",        "EE.UU."}):         "2026-06-25",
    frozenset({"Paraguay",       "Australia"}):      "2026-06-25",

    # ─── GRUPO E ──────────────────────────────────────────────────────────────
    frozenset({"Alemania",       "Curazao"}):        "2026-06-14",
    frozenset({"Costa de Marfil","Ecuador"}):        "2026-06-14",
    frozenset({"Alemania",       "Costa de Marfil"}): "2026-06-20",
    frozenset({"Ecuador",        "Curazao"}):        "2026-06-20",
    frozenset({"Curazao",        "Costa de Marfil"}): "2026-06-25",
    frozenset({"Ecuador",        "Alemania"}):       "2026-06-25",

    # ─── GRUPO F ──────────────────────────────────────────────────────────────
    frozenset({"Países Bajos",   "Japón"}):          "2026-06-14",
    frozenset({"Suecia",         "Túnez"}):          "2026-06-14",
    frozenset({"Países Bajos",   "Suecia"}):         "2026-06-20",
    frozenset({"Japón",          "Túnez"}):          "2026-06-20",
    frozenset({"Japón",          "Suecia"}):         "2026-06-25",
    frozenset({"Túnez",          "Países Bajos"}):   "2026-06-25",

    # ─── GRUPO G ──────────────────────────────────────────────────────────────
    frozenset({"Bélgica",        "Egipto"}):         "2026-06-15",
    frozenset({"Irán",           "Nueva Zelanda"}):  "2026-06-15",
    frozenset({"Bélgica",        "Irán"}):           "2026-06-21",
    frozenset({"Nueva Zelanda",  "Egipto"}):         "2026-06-21",
    frozenset({"Egipto",         "Irán"}):           "2026-06-26",
    frozenset({"Nueva Zelanda",  "Bélgica"}):        "2026-06-26",

    # ─── GRUPO H ──────────────────────────────────────────────────────────────
    frozenset({"España",         "Cabo Verde"}):     "2026-06-15",
    frozenset({"Arabia Saudí",   "Uruguay"}):        "2026-06-15",
    frozenset({"España",         "Arabia Saudí"}):   "2026-06-21",
    frozenset({"Uruguay",        "Cabo Verde"}):     "2026-06-21",
    frozenset({"Cabo Verde",     "Arabia Saudí"}):   "2026-06-26",
    frozenset({"Uruguay",        "España"}):         "2026-06-26",

    # ─── GRUPO I ──────────────────────────────────────────────────────────────
    frozenset({"Francia",        "Senegal"}):        "2026-06-16",
    frozenset({"Irak",           "Noruega"}):        "2026-06-16",
    frozenset({"Francia",        "Irak"}):           "2026-06-22",
    frozenset({"Noruega",        "Senegal"}):        "2026-06-22",
    frozenset({"Noruega",        "Francia"}):        "2026-06-26",
    frozenset({"Senegal",        "Irak"}):           "2026-06-26",

    # ─── GRUPO J ──────────────────────────────────────────────────────────────
    frozenset({"Argentina",      "Argelia"}):        "2026-06-16",
    frozenset({"Austria",        "Jordania"}):       "2026-06-16",
    frozenset({"Argentina",      "Austria"}):        "2026-06-22",
    frozenset({"Jordania",       "Argelia"}):        "2026-06-22",
    frozenset({"Argelia",        "Austria"}):        "2026-06-27",
    frozenset({"Jordania",       "Argentina"}):      "2026-06-27",

    # ─── GRUPO K ──────────────────────────────────────────────────────────────
    frozenset({"Portugal",       "RD Congo"}):       "2026-06-17",
    frozenset({"Uzbekistán",     "Colombia"}):       "2026-06-17",
    frozenset({"Portugal",       "Uzbekistán"}):     "2026-06-23",
    frozenset({"Colombia",       "RD Congo"}):       "2026-06-23",
    frozenset({"Colombia",       "Portugal"}):       "2026-06-27",
    frozenset({"RD Congo",       "Uzbekistán"}):     "2026-06-27",

    # ─── GRUPO L ──────────────────────────────────────────────────────────────
    frozenset({"Inglaterra",     "Croacia"}):        "2026-06-17",
    frozenset({"Ghana",          "Panamá"}):         "2026-06-17",
    frozenset({"Inglaterra",     "Ghana"}):          "2026-06-23",
    frozenset({"Panamá",         "Croacia"}):        "2026-06-23",
    frozenset({"Panamá",         "Inglaterra"}):     "2026-06-27",
    frozenset({"Croacia",        "Ghana"}):          "2026-06-27",
}


def generar_calendario_hardcoded(grupos: dict[str, list[str]]) -> list[dict]:
    """Genera el calendario de 72 partidos con sede y fecha correcta por partido."""
    partidos = []
    for grupo, equipos in grupos.items():
        fechas_grupo = FECHAS_JORNADAS.get(grupo, {1: "TBD", 2: "TBD", 3: "TBD"})
        for jornada, i, j in MATCHDAY_PAIRS:
            eq1, eq2 = equipos[i], equipos[j]
            sede, estadio = SEDES_PARTIDOS.get(frozenset({eq1, eq2}), ("TBD", "TBD"))
            # Fecha exacta por partido; fallback a la fecha de jornada del grupo
            fecha = FECHAS_PARTIDOS.get(
                frozenset({eq1, eq2}),
                fechas_grupo.get(jornada, "TBD")
            )
            if sede == "TBD":
                logger.warning(f"Sede no encontrada para {eq1} vs {eq2}")
            partidos.append({
                "grupo":   grupo,
                "jornada": jornada,
                "equipo1": eq1,
                "equipo2": eq2,
                "fecha":   fecha,
                "hora":    "TBD",
                "sede":    sede,
                "estadio": estadio,
            })
    partidos.sort(key=lambda p: (
        p["fecha"] if p["fecha"] != "TBD" else "9999-99-99",
        p["grupo"], p["jornada"]
    ))
    return partidos


async def obtener_calendario_fifa(grupos: dict[str, list[str]]) -> Optional[list[dict]]:
    """Placeholder — usa fallback hardcoded."""
    return None


def get_calendario(grupos: dict[str, list[str]], usar_fifa: bool = True) -> list[dict]:
    """Punto de entrada. Devuelve los 72 partidos de fase de grupos."""
    return generar_calendario_hardcoded(grupos)
