#!/usr/bin/env python3
"""
Script de prueba para verificar el formateo de pares de trading
"""

import sys
from config import Config

# Soporte para emojis en consola Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def test_trading_pair_formatting():
    """Prueba la función de formateo de pares de trading"""
    
    test_cases = [
        ('BTCUSDT', 'BTC-USDT'),
        ('ETHUSDT', 'ETH-USDT'),
        ('AVAXUSDT', 'AVAX-USDT'),
        ('ADAUSDT', 'ADA-USDT'),
        ('SOLUSDT', 'SOL-USDT'),
        ('DOTUSDT', 'DOT-USDT'),
        ('LINKUSDT', 'LINK-USDT'),
        ('MATICUSDT', 'MATIC-USDT'),
        ('BTCETH', 'BTC-ETH'),
        ('ETHBNB', 'ETH-BNB'),
        ('BTC-USDT', 'BTC-USDT'),  # Par ya formateado no debe convertirse en BTC--USDT
        ('ETH-USDC', 'ETH-USDC'),  # Par ya formateado con guion
        ('UNKNOWN', 'UNKNOWN')      # Caso donde no se encuentra moneda base conocida
    ]
    
    print("🧪 Probando formateo de pares de trading...")
    print("=" * 50)
    
    all_passed = True
    
    for original, expected in test_cases:
        result = Config.format_trading_pair(original)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        print(f"{original:12} -> {result:12} | {status}")
        
        if result != expected:
            print(f"   Esperado: {expected}")
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("🎉 Todas las pruebas pasaron correctamente!")
    else:
        print("⚠️  Algunas pruebas fallaron.")
    
    return all_passed

if __name__ == "__main__":
    test_trading_pair_formatting()
