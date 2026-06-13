"""
config.py
Rutas, zona horaria, parámetros del modelo y constantes de configuración.
"""
import os
from pathlib import Path
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------------
# Rutas base — ajustar si el proyecto se mueve
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "Mundial"
GRAFICOS_DIR = OUTPUT_DIR / "graficos"
LOGS_DIR = BASE_DIR / "logs"
CACHE_DIR = BASE_DIR / ".cache"

# CSV outputs
CSV_FASE_GRUPOS = OUTPUT_DIR / "mundial2026_partidos_fase_grupos.csv"
CSV_PRONOSTICADOR = OUTPUT_DIR / "mundial2026_tabla_rondas.csv"
CSV_ELOS = OUTPUT_DIR / "mundial2026_elos.csv"
JSON_CACHE_ELOS = CACHE_DIR / "elos_anterior.json"
JSON_CACHE_PROBS = CACHE_DIR / "probs_anterior.json"

# Crear directorios si no existen
for _d in [OUTPUT_DIR, GRAFICOS_DIR, LOGS_DIR, CACHE_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Zona horaria y programación
# ---------------------------------------------------------------------------
TZ_MADRID = ZoneInfo("Europe/Madrid")
HORA_EJECUCION = "09:00"   # hora local Madrid para la tarea programada

# ---------------------------------------------------------------------------
# Parámetros del modelo
# ---------------------------------------------------------------------------
N_SIMULACIONES = 100_000

# Draw rate: puntos de calibración (|ΔElo|, P_empate)
DRAW_CALIBRATION = [
    (0,   0.330),
    (100, 0.270),
    (200, 0.200),
    (300, 0.135),
    (400, 0.075),
    (600, 0.025),
]

# Validaciones
MIN_EQUIPOS_REQUERIDOS = 40       # mínimo de Elos extraídos para continuar
ELO_MIN, ELO_MAX = 1200, 2300    # rango válido de Elo
MAX_CAMBIO_ELO_DIARIO = 9999     # sin restricción de variación diaria

# ---------------------------------------------------------------------------
# Google Sheets / Docs
# ---------------------------------------------------------------------------
# Ruta al JSON de credenciales de la cuenta de servicio de Google
# Obtener en: https://console.cloud.google.com → IAM → Cuentas de servicio
GOOGLE_CREDENTIALS_PATH = BASE_DIR / "credentials" / "service_account.json"

# ID del Google Spreadsheet 'Predicciones del Mundial'
# Extraer de la URL: https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/...
SPREADSHEET_ID = "1fpERkNXWfkwV3DfMo6Lyh22iPX-5jO8544gFk-APRZE"   # Google Sheets
DOCUMENT_ID    = "1onbWlpqUkZHZXNLieL9p8oB6Q4YuHGysDDOl4hTNP9o"   # Google Docs — pegar aquí el ID del doc

# Nombres de las pestañas
SHEET_PRONOSTICADOR   = "Pronosticador"
SHEET_FASE_GRUPOS     = "Fase de grupos"
SHEET_DIECISEISAVOS   = "Dieciseisavos"
SHEET_OCTAVOS         = "Octavos"
SHEET_CUARTOS         = "Cuartos"
SHEET_SEMIS           = "Semifinales"
SHEET_TERCER_CUARTO   = "Tercer y cuarto puesto"
SHEET_FINAL           = "Final"
SHEET_TEXTO_METODO    = "Texto método"

# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------
URL_ELO = "https://eloratings.net/"
PLAYWRIGHT_TIMEOUT_MS = 60_000    # 60 s de espera máxima
PLAYWRIGHT_HEADLESS = True

# ---------------------------------------------------------------------------
# Visualización (gráficos PNG)
# ---------------------------------------------------------------------------
COLOR_FONDO     = "#0a0a0f"
COLOR_TEXTO     = "#ffffff"
COLOR_DORADO    = "#e8c547"
COLOR_EMPATE    = "#3a3a52"
COLOR_VISITANTE = "#5b8dee"
PNG_DPI         = 200
PNG_SIZE_INCHES = (6.4, 6.03)  # ~1280×1206 px (ref. 640×603 × 2)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_MAX_BYTES   = 5 * 1024 * 1024   # 5 MB
LOG_BACKUP_COUNT = 30               # 30 ficheros de rotac