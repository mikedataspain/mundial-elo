"""
generar_snapshot_csv.py
Lee data.csv del repo y genera snapshots/YYYY-MM-DD.png.
Se llama desde actualizar-mundial.ps1 después de copiar el CSV.
"""

import sys
from datetime import date
from pathlib import Path

import pandas as pd

repo = Path(__file__).parent
sys.path.insert(0, str(repo))

from snapshot import generar_snapshot

hoy = date.today().isoformat()
csv_path = repo / "data.csv"

if not csv_path.exists():
    print(f"ERROR: no se encontró {csv_path}", file=sys.stderr)
    sys.exit(1)

df = pd.read_csv(csv_path, encoding="utf-8-sig")

# Asegurar orden por Campeón% desc (igual que en el modelo)
if "Campeón%" in df.columns:
    df = df.sort_values("Campeón%", ascending=False).reset_index(drop=True)

snap_path = repo / "snapshots" / f"{hoy}.png"
generar_snapshot(df, hoy, snap_path)
print(f"Snapshot guardado: {snap_path}")
