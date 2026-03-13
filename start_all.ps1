# Script para iniciar todos los servicios del Sistema USDA
# Ejecutar desde la raíz del proyecto: .\start_all.ps1

Write-Host "🚀 Iniciando Sistema USDA..." -ForegroundColor Cyan
Write-Host ""

$projectRoot = Get-Location

# Verificar que estamos en la raíz del proyecto
if (-not (Test-Path "backend") -or -not (Test-Path "frontend")) {
    Write-Host "❌ Error: Ejecute este script desde la raíz del proyecto" -ForegroundColor Red
    Write-Host "   cd C:\proyecto_usda" -ForegroundColor Yellow
    Write-Host "   .\start_all.ps1" -ForegroundColor Yellow
    exit 1
}

# 1. Backend Django
Write-Host "1️⃣  Iniciando Backend Django..." -ForegroundColor Green
$backendCmd = "cd '$projectRoot\backend'; venv\Scripts\activate; python manage.py runserver"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

Start-Sleep -Seconds 2

# 2. Frontend React
Write-Host "2️⃣  Iniciando Frontend React..." -ForegroundColor Green
$frontendCmd = "cd '$projectRoot\frontend'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Start-Sleep -Seconds 2

# 3. Servicio Zebra
Write-Host "3️⃣  Iniciando Servicio de Impresión Zebra..." -ForegroundColor Green
$zebraCmd = "cd '$projectRoot'; python zebra_print_service.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $zebraCmd

Start-Sleep -Seconds 3

# Resumen
Write-Host ""
Write-Host "✅ Todos los servicios han sido iniciados" -ForegroundColor Green
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "📱 URLs de Acceso:" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Frontend:  " -NoNewline; Write-Host "http://localhost:5173" -ForegroundColor Yellow
Write-Host "  Backend:   " -NoNewline; Write-Host "http://localhost:8000/admin" -ForegroundColor Yellow
Write-Host "  Zebra:     " -NoNewline; Write-Host "http://localhost:5000/health" -ForegroundColor Yellow
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host ""
Write-Host "💡 Consejo: " -NoNewline -ForegroundColor Cyan
Write-Host "Abre http://localhost:5173 en tu navegador"
Write-Host ""
Write-Host "⚠️  Para detener los servicios, cierra las ventanas de PowerShell" -ForegroundColor Yellow
Write-Host ""
