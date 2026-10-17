"""
Bot de Telegram para enviar notificaciones de trading
"""

import asyncio
import aiohttp
import logging
import ssl
import certifi
from typing import Optional
import time

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.max_retries = 3
        self.retry_delay = 2  # segundos
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def get_session(self) -> aiohttp.ClientSession:
        """Obtiene o crea una sesión HTTP con soporte SSL robusto"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                ttl_dns_cache=300,
                use_dns_cache=True,
                limit=10,
                limit_per_host=5
            )
            self.session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self.session

    async def close(self):
        """Cierra la sesión HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()
            # Breve pausa para permitir que el loop de eventos cierre los sockets SSL
            await asyncio.sleep(0.25)
            
    async def send_message(self, message: str, parse_mode: str = "Markdown", reply_markup: Optional[dict] = None) -> bool:
        """
        Envía un mensaje a través del bot de Telegram con reintentos y fallback
        
        Args:
            message: Mensaje a enviar
            parse_mode: Formato del mensaje (Markdown o HTML)
            reply_markup: Teclado inline o de respuesta (opcional)
            
        Returns:
            bool: True si el mensaje se envió correctamente
        """
        if not self.bot_token or not self.chat_id:
            logger.error("TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no están configurados.")
            return False

        url = f"{self.base_url}/sendMessage"
        
        payload = {
            'chat_id': self.chat_id,
            'text': message,
        }
        if parse_mode:
            payload['parse_mode'] = parse_mode
        
        if reply_markup:
            payload['reply_markup'] = reply_markup
        
        for attempt in range(self.max_retries):
            try:
                session = await self.get_session()
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Mensaje enviado exitosamente a Telegram")
                        return True
                    elif response.status == 429:  # Rate limit
                        retry_after = int(response.headers.get("Retry-After", 5))
                        logger.warning(f"Rate limit de Telegram. Reintentando en {retry_after}s")
                        await asyncio.sleep(retry_after)
                    elif response.status == 400 and payload.get('parse_mode'):
                        # Fallback: Telegram puede fallar si hay caracteres especiales en Markdown
                        error_text = await response.text()
                        logger.warning(f"Error 400 con parse_mode '{parse_mode}': {error_text}. Reintentando como texto plano...")
                        payload_plain = dict(payload)
                        payload_plain.pop('parse_mode', None)
                        async with session.post(url, json=payload_plain) as retry_response:
                            if retry_response.status == 200:
                                logger.info("Mensaje enviado exitosamente a Telegram en texto plano")
                                return True
                            else:
                                plain_err = await retry_response.text()
                                logger.error(f"Error enviando mensaje en texto plano: {retry_response.status} - {plain_err}")
                                return False
                    else:
                        error_text = await response.text()
                        logger.error(f"Error enviando mensaje a Telegram: {response.status} - {error_text}")
                        if response.status >= 500: # Solo reintentar errores de servidor
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                        else:
                            return False
                            
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                logger.warning(f"Error de conexión en intento {attempt + 1}/{self.max_retries}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                    
            except Exception as e:
                logger.error(f"Error inesperado enviando mensaje: {e}")
                break
                    
        logger.error(f"Falló el envío después de {self.max_retries} intentos")
        return False
    
    async def send_photo(self, photo_url: str, caption: str = "", reply_markup: Optional[dict] = None) -> bool:
        """
        Envía una foto a través del bot de Telegram
        
        Args:
            photo_url: URL de la imagen
            caption: Descripción de la imagen
            reply_markup: Teclado inline o de respuesta (opcional)
            
        Returns:
            bool: True si la imagen se envió correctamente
        """
        url = f"{self.base_url}/sendPhoto"
        
        payload = {
            'chat_id': self.chat_id,
            'photo': photo_url,
            'caption': caption,
            'parse_mode': 'Markdown'
        }
        
        if reply_markup:
            payload['reply_markup'] = reply_markup
        
        try:
            session = await self.get_session()
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info("Imagen enviada exitosamente a Telegram")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Error enviando imagen a Telegram: {response.status} - {error_text}")
                    return False
                        
        except Exception as e:
            logger.error(f"Excepción enviando imagen a Telegram: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """
        Prueba la conexión con el bot de Telegram con reintentos
        
        Returns:
            bool: True si la conexión es exitosa
        """
        url = f"{self.base_url}/getMe"
        
        for attempt in range(self.max_retries):
            try:
                session = await self.get_session()
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        bot_info = data.get('result', {})
                        logger.info(f"Conexión exitosa con bot: {bot_info.get('username', 'Unknown')}")
                        return True
                    else:
                        logger.error(f"Error probando conexión: {response.status}")
                            
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                logger.warning(f"Error de conexión en intento {attempt + 1}/{self.max_retries}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                    
            except Exception as e:
                logger.error(f"Error inesperado probando conexión: {e}")
                break
                    
        logger.error(f"Falló la conexión después de {self.max_retries} intentos")
        return False
