#!/usr/bin/env python3
"""
Script de prueba específico para conectividad con Telegram
"""

import sys
import asyncio
import logging
from config import Config
from telegram_bot import TelegramBot

# Soporte para emojis en consola Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_telegram_detailed():
    """Prueba detallada de conectividad con Telegram"""
    print("🔍 Probando conectividad con Telegram...")
    
    config = Config()
    telegram_bot = TelegramBot(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
    
    token_preview = config.TELEGRAM_BOT_TOKEN[:10] if config.TELEGRAM_BOT_TOKEN else "NO_CONFIGURADO"
    print(f"Bot Token: {token_preview}...")
    print(f"Chat ID: {config.TELEGRAM_CHAT_ID}")
    
    try:
        # Probar conexión básica
        print("\n1. Probando conexión básica...")
        success = await telegram_bot.test_connection()
        
        if success:
            print("✅ Conexión básica exitosa")
            
            # Probar envío de mensaje
            print("\n2. Probando envío de mensaje...")
            message_success = await telegram_bot.send_message("🧪 *Prueba de conectividad*\n\nEste es un mensaje de prueba para verificar que el bot funciona correctamente.")
            
            if message_success:
                print("✅ Mensaje enviado exitosamente")
                return True
            else:
                print("❌ Error enviando mensaje")
                return False
        else:
            print("❌ Error en conexión básica")
            return False
    finally:
        await telegram_bot.close()

if __name__ == "__main__":
    result = asyncio.run(test_telegram_detailed())
    
    if result:
        print("\n🎉 ¡Telegram funciona correctamente!")
    else:
        print("\n⚠️ Hay problemas de conectividad.")
        print("\nPosibles soluciones:")
        print("1. Verificar conexión a internet")
        print("2. Verificar configuración de proxy/firewall")
        print("3. Intentar usar VPN si hay restricciones regionales")
        print("4. Verificar que el token y chat ID sean correctos")
