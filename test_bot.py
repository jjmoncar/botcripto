#!/usr/bin/env python3
"""
Script de prueba para el Bot de Trading
"""

import sys
import asyncio
import logging
from config import Config
from telegram_bot import TelegramBot
from data_fetcher import DataFetcher
from market_analyzer import MarketAnalyzer

# Soporte para emojis en consola Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Configurar logging para pruebas
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_telegram_connection():
    """Prueba la conexión con Telegram"""
    print("🔍 Probando conexión con Telegram...")
    
    config = Config()
    telegram_bot = TelegramBot(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
    
    try:
        # Probar conexión
        success = await telegram_bot.test_connection()
        if success:
            print("✅ Conexión con Telegram exitosa")
            # Enviar mensaje de prueba
            await telegram_bot.send_message("🧪 *Mensaje de prueba*\n\nEl bot está funcionando correctamente!")
            return True
        else:
            print("❌ Error conectando con Telegram")
            return False
    finally:
        await telegram_bot.close()

async def test_data_fetching():
    """Prueba la obtención de datos de mercado"""
    print("🔍 Probando obtención de datos de mercado...")
    
    data_fetcher = DataFetcher()
    try:
        # Probar con BTCUSDT
        market_data = await data_fetcher.get_market_data('BTCUSDT', '1h', 50)
        
        if market_data:
            print(f"✅ Datos obtenidos para BTCUSDT:")
            print(f"   - Precio actual: ${market_data['current_price']:.2f}")
            print(f"   - Datos históricos: {len(market_data['data'])} puntos")
            return True
        else:
            print("❌ Error obteniendo datos de mercado")
            return False
    finally:
        await data_fetcher.close_session()

async def test_market_analysis():
    """Prueba el análisis de mercado Swing"""
    print("🔍 Probando análisis de mercado (Swing 1h)...")
    
    data_fetcher = DataFetcher()
    market_analyzer = MarketAnalyzer()
    
    try:
        # Obtener datos 1h
        market_data = await data_fetcher.get_market_data('BTCUSDT', '1h', 100)
        
        if not market_data:
            print("❌ No se pudieron obtener datos para análisis Swing")
            return False
        
        # Analizar
        signal = market_analyzer.analyze(market_data, 'BTCUSDT', timeframe='1h')
        
        if signal:
            print(f"✅ Señal Swing generada para BTCUSDT:")
            print(f"   - Dirección: {signal['direction']}")
            print(f"   - Probabilidad: {signal['probability']:.1f}%")
            print(f"   - Stop Loss: ${signal['stop_loss']:.2f}")
            print(f"   - Take Profit: ${signal['take_profit']:.2f}")
        else:
            print("ℹ️  No se generó señal Swing (normal si no hay condiciones de trading)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en análisis Swing: {e}")
        return False
    finally:
        await data_fetcher.close_session()

async def test_scalping_analysis():
    """Prueba el análisis de mercado para Scalping (5m)"""
    print("🔍 Probando análisis de mercado (Scalping 5m)...")
    
    data_fetcher = DataFetcher()
    market_analyzer = MarketAnalyzer()
    
    try:
        # Obtener datos 5m
        market_data = await data_fetcher.get_market_data('BTCUSDT', '5m', 100)
        
        if not market_data:
            print("❌ No se pudieron obtener datos para análisis Scalping")
            return False
        
        # Analizar
        signal = market_analyzer.analyze(market_data, 'BTCUSDT', timeframe='5m')
        
        if signal:
            print(f"✅ Señal Scalping generada para BTCUSDT (5m):")
            print(f"   - Dirección: {signal['direction']}")
            print(f"   - Probabilidad: {signal['probability']:.1f}%")
            print(f"   - Stop Loss: ${signal['stop_loss']:.2f}")
            print(f"   - TP1: ${signal.get('take_profit_1', 0):.2f}")
            print(f"   - TP Final: ${signal['take_profit']:.2f}")
        else:
            print("ℹ️  No se generó señal Scalping (normal si no hay condiciones en 5m)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en análisis Scalping: {e}")
        return False
    finally:
        await data_fetcher.close_session()

async def run_tests():
    """Ejecuta todas las pruebas"""
    print("🚀 Iniciando pruebas del Bot de Trading...\n")
    
    tests = [
        ("Conexión Telegram", test_telegram_connection),
        ("Datos de mercado", test_data_fetching),
        ("Análisis Swing (1h)", test_market_analysis),
        ("Análisis Scalping (5m)", test_scalping_analysis)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"PRUEBA: {test_name}")
        print(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en prueba {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen
    print(f"\n{'='*50}")
    print("RESUMEN DE PRUEBAS")
    print(f"{'='*50}")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{len(results)} pruebas pasaron")
    
    if passed == len(results):
        print("\n🎉 ¡Todas las pruebas pasaron! El bot está listo para usar.")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisa la configuración.")

if __name__ == "__main__":
    asyncio.run(run_tests())
