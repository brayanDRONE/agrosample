#!/usr/bin/env python3
"""Inicia sesión en Descolgados y confirma acceso al listado de detecciones."""

import argparse
import asyncio
import getpass
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv, set_key
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"
LOGIN_URL = "https://descolgados.sag.gob.cl/login.asp"
LIST_PATH = "/SQL_Descolga_LEFTlist.asp"


def configure_credentials():
    username = getpass.getpass("Usuario Descolgados (entrada oculta): ").strip()
    password = getpass.getpass("Contraseña Descolgados (entrada oculta): ")
    if not username or not password:
        raise RuntimeError("Usuario y contraseña no pueden estar vacíos.")

    set_key(str(ENV_FILE), "DESCOLGADOS_USERNAME", username, quote_mode="always")
    set_key(str(ENV_FILE), "DESCOLGADOS_PASSWORD", password, quote_mode="always")
    print("Credenciales guardadas en .env local (archivo ignorado por Git).")


def get_credentials():
    load_dotenv(ENV_FILE)
    username = os.getenv("DESCOLGADOS_USERNAME")
    password = os.getenv("DESCOLGADOS_PASSWORD")
    if not username or not password:
        raise RuntimeError(
            "Configura DESCOLGADOS_USERNAME y DESCOLGADOS_PASSWORD en el archivo .env local."
        )
    return username, password


async def has_detection_list(page):
    return await page.get_by_text(
        "LISTADO DE DETECCIONES TEMPORADA", exact=False
    ).count() > 0


async def login(page, username, password):
    response = await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    if response and response.status >= 400:
        raise RuntimeError(f"El portal respondió HTTP {response.status} al abrir el acceso.")

    if await has_detection_list(page):
        return page.url

    username_input = page.locator("#username")
    password_input = page.locator("#password")
    if await username_input.count() == 0 or await password_input.count() == 0:
        raise RuntimeError("No se encontraron los campos de acceso esperados en el portal.")

    await username_input.fill(username)
    await password_input.fill(password)
    await page.locator("#submit").click()

    try:
        await page.wait_for_url(f"**{LIST_PATH}**", timeout=15000)
    except PlaywrightTimeoutError as error:
        if not await has_detection_list(page):
            raise RuntimeError(
                "El portal no abrió el listado; revisa las credenciales o el estado del servicio."
            ) from error

    await page.get_by_text(
        "LISTADO DE DETECCIONES TEMPORADA", exact=False
    ).wait_for(state="visible", timeout=10000)
    return page.url


async def run(headless):
    username, password = get_credentials()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)
        context = await browser.new_context()
        try:
            page = await context.new_page()
            list_url = await login(page, username, password)
            print("Inicio de sesión correcto; listado de detecciones disponible.")
            print(f"Ruta: {urlsplit(list_url).path}")
        finally:
            await context.close()
            await browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--configure-credentials",
        action="store_true",
        help="Guardar credenciales en .env local usando entrada oculta.",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Mostrar Chromium durante el inicio de sesión.",
    )
    args = parser.parse_args()
    try:
        if args.configure_credentials:
            configure_credentials()
            return
        asyncio.run(run(headless=not args.headed))
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()