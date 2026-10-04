#!/usr/bin/env bash
# Script de build para Render

set -o errexit

# Ir al directorio backend
cd backend

echo "Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Creando directorio de archivos estáticos..."
mkdir -p staticfiles

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --no-input --clear

echo "Build completado exitosamente!"
