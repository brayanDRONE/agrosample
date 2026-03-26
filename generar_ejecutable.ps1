# ============================================
# GENERADOR DE EJECUTABLE
# Crea un archivo .exe standalone del servicio de impresión
# ============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GENERADOR DE EJECUTABLE - ZEBRA SERVICE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar que Python esté instalado
Write-Host "[1/6] Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "  ✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Python no encontrado. Instale Python 3.8+" -ForegroundColor Red
    exit 1
}

# 2. Instalar PyInstaller
Write-Host ""
Write-Host "[2/6] Instalando PyInstaller..." -ForegroundColor Yellow
pip install pyinstaller pillow pystray pywin32

# 3. Crear archivo spec personalizado
Write-Host ""
Write-Host "[3/6] Creando configuración..." -ForegroundColor Yellow

$specContent = @"
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['zebra_print_service_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['win32print', 'win32con', 'pywintypes'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ServicioImpresionZebra',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Sin ventana de consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Aquí puedes agregar un icono .ico
    version_file=None,
)
"@

$specContent | Out-File -FilePath "zebra_service.spec" -Encoding utf8
Write-Host "  ✅ Archivo .spec creado" -ForegroundColor Green

# 4. Compilar a .exe
Write-Host ""
Write-Host "[4/6] Compilando a ejecutable..." -ForegroundColor Yellow
Write-Host "  (Esto puede tomar varios minutos)" -ForegroundColor Gray
python -m PyInstaller --clean zebra_service.spec

if (Test-Path "dist\ServicioImpresionZebra.exe") {
    Write-Host "  ✅ Ejecutable creado exitosamente" -ForegroundColor Green
} else {
    Write-Host "  ❌ Error al crear ejecutable" -ForegroundColor Red
    exit 1
}

# 5. Crear carpeta de distribución
Write-Host ""
Write-Host "[5/6] Creando paquete de distribución..." -ForegroundColor Yellow

$distFolder = "ZebraServiceInstaller"
if (Test-Path $distFolder) {
    Remove-Item $distFolder -Recurse -Force
}
New-Item -ItemType Directory -Path $distFolder | Out-Null

# Copiar ejecutable
Copy-Item "dist\ServicioImpresionZebra.exe" "$distFolder\"

# Crear README para usuarios
$readmeContent = @"
================================================
  SERVICIO DE IMPRESIÓN ZEBRA - SAG-USDA
================================================

INSTALACIÓN:
1. Ejecute "ServicioImpresionZebra.exe"
2. Aparecerá un icono verde en la bandeja del sistema (junto al reloj)
3. ¡Listo! Ya puede usar el sistema web

USO:
- El servicio se ejecuta en segundo plano
- Haga clic derecho en el icono verde para ver opciones
- Para salir, clic derecho → "Salir"

REQUISITOS:
- Windows 10 o superior
- Impresora Zebra conectada (USB o Red)
- Internet activa para acceder al sistema web

AYUDA:
- Clic derecho en icono → "Ver Estado" para verificar impresoras
- Clic derecho en icono → "Prueba de Impresión" para probar

SOPORTE:
Contacte al administrador del sistema si tiene problemas.

Versión 1.0 - 2026
"@

$readmeContent | Out-File -FilePath "$distFolder\LEEME.txt" -Encoding utf8
Write-Host "  ✅ Paquete creado en carpeta '$distFolder'" -ForegroundColor Green

# 6. Crear instalador automático
Write-Host ""
Write-Host "[6/6] Creando instalador automático..." -ForegroundColor Yellow

$installerContent = @'
@echo off
echo ================================================
echo   INSTALADOR - SERVICIO IMPRESION ZEBRA
echo ================================================
echo.

REM Verificar permisos de administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Ejecutando con permisos de administrador...
    set INSTALL_DIR=%ProgramFiles%\ZebraServiceUSDA
) else (
    echo NOTA: Sin permisos de administrador.
    echo Instalando en carpeta de usuario...
    set INSTALL_DIR=%LOCALAPPDATA%\ZebraServiceUSDA
)

echo Instalando en: %INSTALL_DIR%
echo.

REM Crear directorio si no existe
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    if errorlevel 1 (
        echo ERROR: No se pudo crear el directorio.
        echo Por favor, ejecute como Administrador.
        pause
        exit /b 1
    )
)

REM Copiar ejecutable
echo Copiando archivos...
copy /Y ServicioImpresionZebra.exe "%INSTALL_DIR%\"
if errorlevel 1 (
    echo ERROR: No se pudo copiar el ejecutable.
    pause
    exit /b 1
)

REM Crear acceso directo en Inicio
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
echo Configurando inicio automatico...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%STARTUP_DIR%\ServicioImpresionZebra.lnk'); $s.TargetPath = '%INSTALL_DIR%\ServicioImpresionZebra.exe'; $s.Save()"

echo.
echo ================================================
echo   INSTALACION COMPLETADA
echo ================================================
echo.
echo Ubicacion: %INSTALL_DIR%
echo El servicio se iniciara automaticamente al reiniciar.
echo.
echo Presione cualquier tecla para iniciar el servicio ahora...
pause > nul

echo.
echo Iniciando servicio...
start "" "%INSTALL_DIR%\ServicioImpresionZebra.exe"

timeout /t 2 /nobreak > nul

echo.
echo Servicio iniciado. Busque el icono verde en la bandeja del sistema.
echo.
pause
'@

$installerContent | Out-File -FilePath "$distFolder\INSTALAR.bat" -Encoding ascii
Write-Host "  ✅ Instalador creado: INSTALAR.bat" -ForegroundColor Green

# 7. Resumen
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GENERACION COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Archivos generados en carpeta: $distFolder" -ForegroundColor White
Write-Host ""
Write-Host "Contenido:" -ForegroundColor Yellow
Write-Host "  - ServicioImpresionZebra.exe  (Ejecutable principal)" -ForegroundColor Gray
Write-Host "  - INSTALAR.bat                (Instalador automatico)" -ForegroundColor Gray
Write-Host "  - LEEME.txt                   (Instrucciones)" -ForegroundColor Gray
Write-Host ""
Write-Host "DISTRIBUCION:" -ForegroundColor Yellow
Write-Host "  1. Comprime la carpeta en un ZIP" -ForegroundColor Gray
Write-Host "  2. Envia el ZIP a cada establecimiento" -ForegroundColor Gray
Write-Host "  3. Los usuarios extraen y ejecutan INSTALAR.bat" -ForegroundColor Gray
Write-Host ""
Write-Host "PRUEBA LOCAL:" -ForegroundColor Yellow
Write-Host "  cd ZebraServiceInstaller" -ForegroundColor Gray
Write-Host '  .\ServicioImpresionZebra.exe' -ForegroundColor Gray
Write-Host ""
