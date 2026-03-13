# Script simple para iniciar todos los servicios
Write-Host "Iniciando Sistema USDA..." -ForegroundColor Cyan

$projectRoot = Get-Location

# Backend Django
Write-Host "Iniciando Backend Django..." -ForegroundColor Green
$backendCmd = "cd '$projectRoot\backend' && venv\Scripts\activate && python manage.py runserver"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
Start-Sleep -Seconds 3

# Frontend React
Write-Host "Iniciando Frontend React..." -ForegroundColor Green
$frontendCmd = "cd '$projectRoot\frontend' && npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd
Start-Sleep -Seconds 3

# Servicio Zebra
Write-Host "Iniciando Servicio Zebra..." -ForegroundColor Green
$zebraCmd = "cd '$projectRoot' && python zebra_print_service.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $zebraCmd
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "Servicios iniciados:" -ForegroundColor Green
Write-Host "Frontend:  http://localhost:5173" -ForegroundColor Yellow
Write-Host "Backend:   http://localhost:8000/admin" -ForegroundColor Yellow
Write-Host "Zebra:     http://localhost:5000/health" -ForegroundColor Yellow
