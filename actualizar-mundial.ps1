# Script de actualización automática - Mundial ELO
# Copia el CSV actualizado y lo sube a GitHub

$proyecto = "C:\Users\magr\OneDrive - Unidad Editorial\Documents\Datasets\Mundial\proyecto-mundial-elo"
$repo     = "C:\Users\magr\OneDrive - Unidad Editorial\Documents\Datasets\Mundial\mundial-elo"
$origen   = "$proyecto\Mundial\mundial2026_tabla_rondas.csv"
$destino  = "$repo\data.csv"

# Verificar que el archivo origen existe
if (-not (Test-Path $origen)) {
    Write-Error "No se encontró el archivo: $origen"
    exit 1
}

# Copiar CSV al repo
Copy-Item $origen -Destination $destino -Force
Write-Host "CSV copiado correctamente."

# Sincronizar modelo.py y resultados.py desde proyecto-mundial-elo
Copy-Item "$proyecto\modelo.py"     -Destination "$repo\modelo.py"     -Force
Copy-Item "$proyecto\resultados.py" -Destination "$repo\resultados.py" -Force
Write-Host "modelo.py y resultados.py sincronizados desde proyecto-mundial-elo."

Set-Location $repo

# Eliminar snapshots no rastreados para que el pull nunca falle por conflicto
$untracked = git ls-files --others --exclude-standard snapshots/
if ($untracked) {
    $untracked | ForEach-Object { Remove-Item $_ -Force -ErrorAction SilentlyContinue }
    Write-Host "Snapshots locales no rastreados eliminados antes del pull."
}

# Pull (ahora sin riesgo de conflicto con snapshots)
git pull --rebase --autostash origin main
if ($LASTEXITCODE -ne 0) {
    Write-Error "git pull --rebase falló. Abortando push."
    git rebase --abort
    exit 1
}

# Generar snapshot del día (después del pull)
py "$repo\generar_snapshot_csv.py"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Snapshot no generado (no bloquea la subida)."
}

git add data.csv snapshots/ modelo.py resultados.py
$fecha = Get-Date -Format "yyyy-MM-dd HH:mm"
git commit -m "Actualización automática $fecha"
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Error "git push falló. Comprueba el estado del repo."
    exit 1
}
Write-Host "Subido a GitHub correctamente."
