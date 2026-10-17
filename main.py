#!/usr/bin/env python3
"""
Bot de Trading de Futuros
Aplicación principal que analiza el mercado y envía señales a Telegram
"""

import sys
import asyncio
import logging
from datetime import datetime, timedelta
from config import Config
from market_analyzer import MarketAnalyzer
from telegram_bot import TelegramBot
from data_fetcher import DataFetcher

# Asegurar soporte para emojis en consola de Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Configurar logging con encoding UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        self.config = Config()
        self.data_fetcher = DataFetcher()
        self.market_analyzer = MarketAnalyzer()
        self.telegram_bot = TelegramBot(self.config.TELEGRAM_BOT_TOKEN, self.config.TELEGRAM_CHAT_ID)
        self.is_running = False
        self.last_signals = {}  # (symbol, timeframe, direction) -> datetime
        
    async def stop(self):
        """Detiene el bot y limpia recursos"""
        self.is_running = False
        logger.info("Cerrando recursos...")
        await self.data_fetcher.close_session()
        await self.telegram_bot.close()
        logger.info("Bot detenido correctamente.")
        
    async def run(self):
        """Ejecuta el bot principal"""
        active_tfs = self.config.get_active_timeframes()
        logger.info(f"Iniciando Bot de Trading de Futuros (Modo: {self.config.TRADING_MODE})...")
        logger.info(f"Timeframes activos: {', '.join(active_tfs)}")
        self.is_running = True
        
        # Enviar mensaje de inicio
        await self.telegram_bot.send_message(
            f"🤖 *Bot de Trading iniciado*\n"
            f"• Modo: *{self.config.TRADING_MODE}*\n"
            f"• Temporalidades: *{', '.join(active_tfs)}*\n"
            f"• Pares monitoreados: *{len(self.config.TRADING_PAIRS)}*"
        )
        
        try:
            while self.is_running:
                try:
                    # Obtener datos de mercado para todos los pares y timeframes configurados
                    for symbol in self.config.TRADING_PAIRS:
                        if not self.is_running:
                            break
                        for timeframe in active_tfs:
                            if not self.is_running:
                                break
                            await self.analyze_symbol(symbol, timeframe)
                            # Pequeña pausa entre solicitudes para evitar rate limits
                            await asyncio.sleep(0.4)
                    
                    if not self.is_running:
                        break
                        
                    # Esperar antes del próximo ciclo de análisis
                    logger.info(f"Ciclo completado. Esperando {self.config.ANALYSIS_INTERVAL}s...")
                    await asyncio.sleep(self.config.ANALYSIS_INTERVAL)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error en el ciclo de análisis: {e}")
                    await asyncio.sleep(60)  # Esperar 1 minuto antes de reintentar
        finally:
            await self.stop()
    
    async def analyze_symbol(self, symbol, timeframe):
        """Analiza un par de monedas específico en un timeframe dado (Scalping o Swing)"""
        try:
            is_scalping = self.config.is_scalping_timeframe(timeframe)
            min_prob = self.config.SCALPING_MIN_PROBABILITY if is_scalping else self.config.MIN_PROBABILITY
            cooldown_mins = self.config.SCALPING_COOLDOWN_MINUTES if is_scalping else self.config.SIGNAL_COOLDOWN_MINUTES
            
            # Obtener datos de mercado (100 velas es óptimo para ambos)
            market_data = await self.data_fetcher.get_market_data(symbol, timeframe, limit=100)
            
            if not market_data:
                return
            
            # Analizar señales especificando timeframe
            signal = self.market_analyzer.analyze(market_data, symbol, timeframe=timeframe)
            
            if signal and signal['probability'] >= min_prob:
                # Comprobar cooldown para evitar duplicados en Telegram
                sig_key = (symbol, timeframe, signal['direction'])
                now = datetime.now()
                cooldown_delta = timedelta(minutes=cooldown_mins)
                
                if sig_key in self.last_signals and (now - self.last_signals[sig_key]) < cooldown_delta:
                    elapsed_min = (now - self.last_signals[sig_key]).total_seconds() / 60
                    logger.debug(f"Señal para {symbol} ({timeframe}) en cooldown ({elapsed_min:.1f}/{cooldown_mins} min). Omitiendo.")
                    return
                
                await self.send_trading_signal(signal)
                self.last_signals[sig_key] = now
                
        except Exception as e:
            logger.error(f"Error analizando {symbol} ({timeframe}): {e}")
    
    async def send_trading_signal(self, signal):
        """Envía señal de trading a Telegram adaptada a Scalping o Swing"""
        try:
            direction_emoji = "📈" if signal['direction'] == 'LONG' else "📉"
            probability_emoji = "🎯" if signal['probability'] >= 75 else "⚡"
            formatted_symbol = self.config.format_trading_pair(signal['symbol'])
            
            curr = signal['current_price']
            sl = signal['stop_loss']
            tp = signal['take_profit']
            tp1 = signal.get('take_profit_1')
            
            sl_pct = abs((sl - curr) / curr) * 100
            tp_pct = abs((tp - curr) / curr) * 100
            tp1_pct = abs((tp1 - curr) / curr) * 100 if tp1 else None
            
            is_scalping = signal.get('mode') == 'SCALPING'
            
            if is_scalping:
                tp1_str = f"🎯 *Take Profit 1:* ${tp1:.4f} (+{tp1_pct:.2f}%)\n" if tp1_pct else ""
                message = f"""
⚡ *SEÑAL SCALPING* ⚡

🎯 *Modalidad:* ⚡ SCALPING (Operación Rápida)
💰 *Par:* {formatted_symbol}
⏱️ *Temporalidad:* {signal.get('timeframe', 'N/A')}
📊 *Dirección:* {signal['direction']} {direction_emoji}
{probability_emoji} *Probabilidad:* {signal['probability']:.1f}%
💵 *Precio entrada:* ${curr:.4f}
🛡️ *Stop Loss:* ${sl:.4f} (-{sl_pct:.2f}%)
{tp1_str}🎯 *Take Profit Final:* ${tp:.4f} (+{tp_pct:.2f}%)

📋 *Indicadores Clave:*
{signal['indicators_summary']}

⏰ *Tiempo:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """.strip()
            else:
                message = f"""
{direction_emoji} *SEÑAL SWING / INTRADÍA* {direction_emoji}

🎯 *Modalidad:* 📈 SWING / TENDENCIAL
💰 *Par:* {formatted_symbol}
⏱️ *Temporalidad:* {signal.get('timeframe', 'N/A')}
📊 *Dirección:* {signal['direction']} {direction_emoji}
{probability_emoji} *Probabilidad:* {signal['probability']:.1f}%
💵 *Precio actual:* ${curr:.4f}
🛡️ *Stop Loss:* ${sl:.4f} (-{sl_pct:.2f}%)
🎯 *Take Profit:* ${tp:.4f} (+{tp_pct:.2f}%)

📋 *Indicadores:*
{signal['indicators_summary']}

⏰ *Tiempo:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """.strip()
            
            # Crear el teclado con el botón de la Mini App (Monetag)
            button_text = "🔓 Desbloquear Análisis Completo" if is_scalping else "🔓 Desbloquear Señal Completa"
            reply_markup = {
                "inline_keyboard": [[
                    {
                        "text": f"{button_text} (Watch Ad)",
                        "url": self.config.MONETAG_MINI_APP_URL
                    }
                ]]
            }
            
            await self.telegram_bot.send_message(message, reply_markup=reply_markup)
            logger.info(f"Señal [{signal.get('mode', 'TRADING')}] enviada para {formatted_symbol} ({signal.get('timeframe')}): {signal['direction']} - {signal['probability']:.1f}%")
            
        except Exception as e:
            logger.error(f"Error enviando señal: {e}")

if __name__ == "__main__":
    bot = TradingBot()
    try:
        asyncio.run(bot.run())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot detenido por el usuario.")
