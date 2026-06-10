"""
equivalencias.py
Tabla de equivalencias: nombre en eloratings.net → castellano.
Incluye todas las variantes conocidas de cada selección.
"""

# ---------------------------------------------------------------------------
# Mapeo eloratings.net (inglés) → castellano
# ---------------------------------------------------------------------------
EQUIVALENCIAS_EN_ES: dict[str, str] = {
    # Grupo A
    "Mexico": "México",
    "South Korea": "Corea del Sur",
    "Korea Republic": "Corea del Sur",
    "Czech Republic": "Rep. Checa",
    "Czechia": "Rep. Checa",
    "South Africa": "Sudáfrica",
    # Grupo B
    "Canada": "Canadá",
    "Bosnia and Herzegovina": "Bosnia-Herz.",
    "Bosnia-Herzegovina": "Bosnia-Herz.",
    "Bosnia & Herzegovina": "Bosnia-Herz.",
    "Bosnia": "Bosnia-Herz.",
    "Qatar": "Qatar",
    "Switzerland": "Suiza",
    # Grupo C
    "Brazil": "Brasil",
    "Morocco": "Marruecos",
    "Haiti": "Haití",
    "Scotland": "Escocia",
    # Grupo D
    "United States": "EE.UU.",
    "USA": "EE.UU.",
    "US": "EE.UU.",
    "Paraguay": "Paraguay",
    "Australia": "Australia",
    "Turkey": "Turquía",
    "Türkiye": "Turquía",
    # Grupo E
    "Germany": "Alemania",
    "Ecuador": "Ecuador",
    "Ivory Coast": "Costa de Marfil",
    "Côte d'Ivoire": "Costa de Marfil",
    "Cote d'Ivoire": "Costa de Marfil",
    "Curaçao": "Curazao",
    "Curacao": "Curazao",
    # Grupo F
    "Netherlands": "Países Bajos",
    "Holland": "Países Bajos",
    "Japan": "Japón",
    "Sweden": "Suecia",
    "Tunisia": "Túnez",
    # Grupo G
    "Belgium": "Bélgica",
    "Iran": "Irán",
    "Egypt": "Egipto",
    "New Zealand": "Nueva Zelanda",
    # Grupo H
    "Spain": "España",
    "Uruguay": "Uruguay",
    "Saudi Arabia": "Arabia Saudí",
    "Cape Verde": "Cabo Verde",
    # Grupo I
    "France": "Francia",
    "Senegal": "Senegal",
    "Iraq": "Irak",
    "Norway": "Noruega",
    # Grupo J
    "Argentina": "Argentina",
    "Algeria": "Argelia",
    "Austria": "Austria",
    "Jordan": "Jordania",
    # Grupo K
    "Portugal": "Portugal",
    "DR Congo": "RD Congo",
    "Congo DR": "RD Congo",
    "Democratic Republic of Congo": "RD Congo",
    "Uzbekistan": "Uzbekistán",
    "Colombia": "Colombia",
    # Grupo L
    "England": "Inglaterra",
    "Croatia": "Croacia",
    "Ghana": "Ghana",
    "Panama": "Panamá",
    # Otras selecciones del ranking (pueden aparecer en la tabla Elo)
    "Italy": "Italia",
    "Denmark": "Dinamarca",
    "Serbia": "Serbia",
    "Ukraine": "Ucrania",
    "Poland": "Polonia",
    "Wales": "Gales",
    "Hungary": "Hungría",
    "Peru": "Perú",
    "Chile": "Chile",
    "Venezuela": "Venezuela",
    "Nigeria": "Nigeria",
    "Cameroon": "Camerún",
    "Mali": "Mali",
    "Costa Rica": "Costa Rica",
    "Honduras": "Honduras",
    "El Salvador": "El Salvador",
    "Jamaica": "Jamaica",
    "Bolivia": "Bolivia",
    "Cuba": "Cuba",
    "Guatemala": "Guatemala",
    "Burkina Faso": "Burkina Faso",
    "Angola": "Angola",
    "North Korea": "Corea del Norte",
    "Korea DPR": "Corea del Norte",
    "China": "China",
    "India": "India",
    "Indonesia": "Indonesia",
    "Thailand": "Tailandia",
    "Vietnam": "Vietnam",
    "Romania": "Rumanía",
    "Greece": "Grecia",
    "Slovakia": "Eslovaquia",
    "Finland": "Finlandia",
    "Iceland": "Islandia",
    "Ireland": "Irlanda",
    "Northern Ireland": "Irlanda del Norte",
    "Luxembourg": "Luxemburgo",
    "North Macedonia": "Macedonia del Norte",
    "Albania": "Albania",
    "Georgia": "Georgia",
    "Armenia": "Armenia",
    "Azerbaijan": "Azerbaiyán",
    "Kazakhstan": "Kazajistán",
    "Belarus": "Bielorrusia",
    "Moldova": "Moldavia",
    "Slovenia": "Eslovenia",
    "Kosovo": "Kosovo",
    "Bulgaria": "Bulgaria",
    "Cyprus": "Chipre",
    "Israel": "Israel",
    "Lebanon": "Líbano",
    "Syria": "Siria",
    "Oman": "Omán",
    "Bahrain": "Baréin",
    "Kuwait": "Kuwait",
    "United Arab Emirates": "Emiratos Árabes",
    "Papua New Guinea": "Papúa Nueva Guinea",
    "Fiji": "Fiyi",
    "Zambia": "Zambia",
    "Zimbabwe": "Zimbabue",
    "Kenya": "Kenia",
    "Tanzania": "Tanzania",
    "Ethiopia": "Etiopía",
    "Libya": "Libia",
    "Sudan": "Sudán",
    "Gambia": "Gambia",
    "Guinea": "Guinea",
    "Mauritania": "Mauritania",
    "Niger": "Níger",
    "Benin": "Benín",
    "Togo": "Togo",
    "Gabon": "Gabón",
    "Mozambique": "Mozambique",
    "Rwanda": "Ruanda",
    "Uganda": "Uganda",
    "Namibia": "Namibia",
    "Botswana": "Botsuana",
    "Lesotho": "Lesoto",
    "Eswatini": "Esuatini",
    "Malawi": "Malaui",
    "Central African Republic": "Rep. Centroafricana",
    "Congo": "Congo",
    "Equatorial Guinea": "Guinea Ecuatorial",
    "Sierra Leone": "Sierra Leona",
    "Liberia": "Liberia",
    "Guinea-Bissau": "Guinea-Bisáu",
    "Dominican Republic": "Rep. Dominicana",
    "Trinidad and Tobago": "Trinidad y Tobago",
    "Trinidad & Tobago": "Trinidad y Tobago",
    "Bermuda": "Bermudas",
    "Barbados": "Barbados",
    "Suriname": "Surinam",
    "Guyana": "Guyana",
    "Nicaragua": "Nicaragua",
    "Honduras": "Honduras",
    "Tahiti": "Tahití",
    "Mongolia": "Mongolia",
    "Palestine": "Palestina",
    "Yemen": "Yemen",
    "Pakistan": "Pakistán",
    "Philippines": "Filipinas",
    "Malaysia": "Malasia",
    "Singapore": "Singapur",
    "Myanmar": "Myanmar",
    "Cambodia": "Camboya",
    "Sri Lanka": "Sri Lanka",
    "Bangladesh": "Bangladesh",
    "Afghanistan": "Afganistán",
    "Nepal": "Nepal",
    "Maldives": "Maldivas",
    "New Caledonia": "Nueva Caledonia",
    "Solomon Islands": "Islas Salomón",
    "Vanuatu": "Vanuatu",
    "Samoa": "Samoa",
    "Tonga": "Tonga",
    "Somalia": "Somalia",
    "Chad": "Chad",
    "Comoros": "Comoras",
    "Madagascar": "Madagascar",
    "Mauritius": "Mauricio",
    "Seychelles": "Seychelles",
    "Djibouti": "Yibuti",
    "Eritrea": "Eritrea",
    "Faroe Islands": "Islas Feroe",
    "Liechtenstein": "Liechtenstein",
    "San Marino": "San Marino",
    "Andorra": "Andorra",
    "Malta": "Malta",
}

# ---------------------------------------------------------------------------
# Lista oficial de las 48 selecciones clasificadas (en castellano)
# ---------------------------------------------------------------------------
EQUIPOS_MUNDIAL_48: list[str] = [
    "México", "Corea del Sur", "Rep. Checa", "Sudáfrica",   # A
    "Canadá", "Bosnia-Herz.", "Qatar", "Suiza",             # B
    "Brasil", "Marruecos", "Haití", "Escocia",              # C
    "EE.UU.", "Paraguay", "Australia", "Turquía",           # D
    "Alemania", "Ecuador", "Costa de Marfil", "Curazao",    # E
    "Países Bajos", "Japón", "Suecia", "Túnez",             # F
    "Bélgica", "Irán", "Egipto", "Nueva Zelanda",           # G
    "España", "Uruguay", "Arabia Saudí", "Cabo Verde",      # H
    "Francia", "Senegal", "Irak", "Noruega",                # I
    "Argentina", "Argelia", "Austria", "Jordania",          # J
    "Portugal", "RD Congo", "Uzbekistán", "Colombia",       # K
    "Inglaterra", "Croacia", "Ghana", "Panamá",             # L
]

# Grupos del Mundial 2026
GRUPOS: dict[str, list[str]] = {
    "A": ["México", "Corea del Sur", "Rep. Checa", "Sudáfrica"],
    "B": ["Canadá", "Bosnia-Herz.", "Qatar", "Suiza"],
    "C": ["Brasil", "Marruecos", "Haití", "Escocia"],
    "D": ["EE.UU.", "Paraguay", "Australia", "Turquía"],
    "E": ["Alemania", "Ecuador", "Costa de Marfil", "Curazao"],
    "F": ["Países Bajos", "Japón", "Suecia", "Túnez"],
    "G": ["Bélgica", "Irán", "Egipto", "Nueva Zelanda"],
    "H": ["España", "Uruguay", "Arabia Saudí", "Cabo Verde"],
    "I": ["Francia", "Senegal", "Irak", "Noruega"],
    "J": ["Argentina", "Argelia", "Austria", "Jordania"],
    "K": ["Portugal", "RD Congo", "Uzbekistán", "Colombia"],
    "L": ["Inglaterra", "Croacia", "Ghana", "Panamá"],
}

# Inverso castellano → nombre canónico eloratings
_es_en_map: dict[str, str] = {}
for _en, _es in EQUIVALENCIAS_EN_ES.items():
    if _es not in _es_en_map:
        _es_en_map[_es] = _en
EQUIVALENCIAS_ES_EN: dict[str, str] = _es_en_map


def a_castellano(nombre_ingles: str) -> str:
    """Convierte nombre de eloratings.net → castellano. Devuelve original si no hay mapeo."""
    nombre_limpio = nombre_ingles.strip()
    resultado = EQUIVALENCIAS_EN_ES.get(nombre_limpio)
    if resultado is None:
        for key, val in EQUIVALENCIAS_EN_ES.items():
            if key.lower() == nombre_limpio.lower():
                return val
        return nombre_limpio
    return resultado


def es_equipo_mundial(nombre_castellano: str) -> bool:
    """True si el nombre está entre los 48 clasificados."""
    return nombre_castellano in EQUIPOS_MUNDIAL_48
