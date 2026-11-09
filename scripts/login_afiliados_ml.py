"""
Abre um navegador visível para você entrar UMA vez no portal de
Afiliados do Mercado Livre. A sessão fica salva em
data/perfil_ml_afiliados e é reutilizada pelo bot (modo headless).

Uso: python scripts/login_afiliados_ml.py
Feche a janela do navegador quando terminar o login.
"""

import asyncio
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from playwright.async_api import async_playwright

from services.afiliados_conversor import PERFIL_ML, URL_GERADOR_ML


async def main():
    PERFIL_ML.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        contexto = await p.chromium.launch_persistent_context(
            str(PERFIL_ML), headless=False, locale="pt-BR"
        )

        page = (
            contexto.pages[0] if contexto.pages else await contexto.new_page()
        )
        await page.goto(URL_GERADOR_ML)

        print("Faça login na janela aberta e feche-a ao terminar.")

        while contexto.pages:
            await asyncio.sleep(1)

        await contexto.close()


asyncio.run(main())
