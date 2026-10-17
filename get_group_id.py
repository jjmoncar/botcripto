#!/usr/bin/env python3
"""
Script para obtener el ID de un grupo de Telegram
"""

import sys
import asyncio
import aiohttp
import ssl
import certifi
import json
from config import Config

# Soporte para emojis en consola Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

async def get_group_id():
    """Obtiene el ID del grupo desde las actualizaciones del bot"""
    config = Config()
    if not config.TELEGRAM_BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN no está configurado en .env")
        return
        
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getUpdates"
    
    print("🔍 Obteniendo actualizaciones del bot...")
    print("📝 Instrucciones:")
    print("1. Agrega tu bot al grupo privado")
    print("2. Envía un mensaje en el grupo mencionando al bot")
    print("3. Ejecuta este script para obtener el ID del grupo")
    print("\n" + "="*50)
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    updates = data.get('result', [])
                    
                    if not updates:
                        print("❌ No hay actualizaciones. Asegúrate de:")
                        print("   - Haber agregado el bot al grupo")
                        print("   - Haber enviado un mensaje en el grupo")
                        return
                    
                    print("📱 Chats encontrados:")
                    print("-" * 50)
                    
                    unique_chats = {}
                    for update in updates:
                        message = update.get('message', {})
                        chat = message.get('chat', {})
                        
                        if chat:
                            chat_id = chat.get('id')
                            chat_type = chat.get('type', 'unknown')
                            chat_title = chat.get('title', chat.get('first_name', 'Sin título'))
                            
                            if chat_id not in unique_chats:
                                unique_chats[chat_id] = {
                                    'type': chat_type,
                                    'title': chat_title
                                }
                    
                    for chat_id, info in unique_chats.items():
                        emoji = "👥" if info['type'] == 'group' else "🔒" if info['type'] == 'supergroup' else "👤"
                        print(f"{emoji} {info['type'].upper()}: {info['title']}")
                        print(f"   ID: {chat_id}")
                        
                        if info['type'] in ['group', 'supergroup']:
                            print(f"   ✅ Usar este ID para el grupo: {chat_id}")
                        print()
                    
                    # Buscar grupos específicamente
                    group_ids = [cid for cid, info in unique_chats.items() 
                               if info['type'] in ['group', 'supergroup']]
                    
                    if group_ids:
                        print("🎯 IDs de grupos encontrados:")
                        for gid in group_ids:
                            print(f"   {gid}")
                        
                        if len(group_ids) == 1:
                            print(f"\n✅ Actualiza tu archivo .env con:")
                            print(f"TELEGRAM_CHAT_ID={group_ids[0]}")
                    else:
                        print("⚠️  No se encontraron grupos. Verifica que:")
                        print("   - El bot esté agregado al grupo")
                        print("   - Hayas enviado un mensaje en el grupo")
                        
                else:
                    print(f"❌ Error obteniendo actualizaciones: {response.status}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_group_id())
