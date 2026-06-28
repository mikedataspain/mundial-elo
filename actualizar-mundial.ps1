# Script de actualización automática - Mundial ELO
# Copia el CSV actualizado y lo sube a GitHub

$origen = "C:\Users\magr\OneDrive - Unidad Editorial\Documents\Datasets\Mundial\proyecto-mundial-elo\Mundial\mundial2026_tabla_rondas.csv"
$repo   = "C:\Users\magr\OneDrive - Unidad Editorial\Documents\Datasets\Mundial\mundial-elo"
$destino = "$repo\data.csv"

# Verificar que el archivo origen existe
if (-not (Test-Path $origen)) {
    Write-Error "No se encontró el archivo: $origen"
    exit 1
}

# Copiar CSV al repo
Copy-Item $origen -Destination $destino -Force
Write-Host "CSV copiado correctamente."

# Generar snapshot del día
py "$repo\generar_snapshot_csv.py"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Snapshot no generado (no bloquea la subida)."
}

# Subir a GitHub
Set-Location $repo
git pull --rebase --autostash origin main
if ($LASTEXITCODE -ne 0) {
    Write-Error "git pull --rebase falló. Abortando push."
    git rebase --abort
    exit 1
}
git add data.csv snapshots/
$fecha = Get-Date -Format "yyyy-MM-dd HH:mm"
git commit -m "Actualización automática $fecha"
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Error "git push falló. Comprueba el estado del repo."
    exit 1
}
Write-Host "Subido a GitHub correctamente."
