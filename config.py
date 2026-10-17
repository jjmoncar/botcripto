"""
Configuración del Bot de Trading
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuración de Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # Configuración de Monetag (Mini App)
    MONETAG_MINI_APP_URL = os.getenv('MONETAG_MINI_APP_URL', 'https://omg10.com/4/10987049')
    
    # Configuración de Exchange (Binance)
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY', '')
    
    # Pares de trading a monitorear
    TRADING_PAIRS = [
        'BTCUSDT',
        'ETHUSDT', 
        'ADAUSDT',
        'SOLUSDT',
        'DOTUSDT',
        'LINKUSDT',
        'AVAXUSDT',
        'BNBUSDT',
        'XRPUSDT',
        'XLMUSDT',
        'TRXUSDT',
        'LTCUSDT'
    ]
    
    # Modo de trading: 'HYBRID' (ambos), 'SCALPING' (solo scalping) o 'SWING' (tendencial)
    TRADING_MODE = os.getenv('TRADING_MODE', 'HYBRID').upper()
    
    # Timeframes para cada modalidad
    SCALPING_TIMEFRAMES = [tf.strip() for tf in os.getenv('SCALPING_TIMEFRAMES', '5m,15m').split(',') if tf.strip()]
    SWING_TIMEFRAMES = [tf.strip() for tf in os.getenv('SWING_TIMEFRAMES', '1h,4h').split(',') if tf.strip()]
    
    # Configuración de análisis general
    # Por defecto 60s si scalping está activo, o 300s para swing
    _default_interval = '60' if TRADING_MODE in ('SCALPING', 'HYBRID') else '300'
    ANALYSIS_INTERVAL = int(os.getenv('ANALYSIS_INTERVAL', _default_interval))
    MIN_PROBABILITY = float(os.getenv('MIN_PROBABILITY', '80.0'))   # Probabilidad mínima swing
    SIGNAL_COOLDOWN_MINUTES = int(os.getenv('SIGNAL_COOLDOWN_MINUTES', '30')) # Cooldown swing
    
    # Configuración específica de Scalping
    SCALPING_MIN_PROBABILITY = float(os.getenv('SCALPING_MIN_PROBABILITY', '75.0')) # Probabilidad mínima scalping
    SCALPING_COOLDOWN_MINUTES = int(os.getenv('SCALPING_COOLDOWN_MINUTES', '10'))  # Cooldown rápido scalping
    SCALPING_STOP_LOSS_PERCENT = float(os.getenv('SCALPING_STOP_LOSS_PERCENT', '0.8'))   # 0.8% stop loss scalping
    SCALPING_TAKE_PROFIT_PERCENT = float(os.getenv('SCALPING_TAKE_PROFIT_PERCENT', '1.6')) # 1.6% take profit scalping
    
    # Configuración de riesgo estándar (Swing / Intradía)
    STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '2.0'))   # 2% stop loss por defecto
    TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', '4.0')) # 4% take profit por defecto
    
    # Configuración de indicadores técnicos
    RSI_PERIOD = 14
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    
    # EMAs rápidas para Scalping (Estrategia EMA 9/21)
    EMA_FAST_SCALPING = 9
    EMA_SLOW_SCALPING = 21
    
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    
    BB_PERIOD = 20
    BB_STD = 2
    
    @classmethod
    def get_active_timeframes(cls) -> list:
        """Devuelve los timeframes activos según el TRADING_MODE configurado"""
        if cls.TRADING_MODE == 'SCALPING':
            return cls.SCALPING_TIMEFRAMES
        elif cls.TRADING_MODE == 'SWING':
            return cls.SWING_TIMEFRAMES
        else:  # HYBRID
            # Combinar asegurando orden de menor a mayor y sin duplicados
            combined = []
            for tf in cls.SCALPING_TIMEFRAMES + cls.SWING_TIMEFRAMES:
                if tf not in combined:
                    combined.append(tf)
            return combined

    @staticmethod
    def is_scalping_timeframe(timeframe: str) -> bool:
        """Determina si una temporalidad corresponde a scalping"""
        return timeframe in ('1m', '3m', '5m', '15m')
    
    # Propiedad de retrocompatibilidad
    @property
    def TIMEFRAMES(self):
        return self.get_active_timeframes()
    
    @staticmethod
    def format_trading_pair(symbol: str) -> str:
        """
        Formatea un par de trading de AVAXUSDT a AVAX-USDT para mejor legibilidad
        
        Args:
            symbol: Par de trading en formato original (ej: AVAXUSDT)
            
        Returns:
            str: Par formateado (ej: AVAX-USDT)
        """
        if not symbol or not isinstance(symbol, str):
            return str(symbol) if symbol is not None else ""
            
        # Si ya está formateado (contiene un guion o barra), devolver tal cual
        if '-' in symbol or '/' in symbol:
            return symbol
            
        # Lista de monedas base comunes para separar correctamente
        base_currencies = ['USDT', 'USDC', 'BTC', 'ETH', 'BNB', 'BUSD']
        
        for base in base_currencies:
            if symbol.endswith(base) and len(symbol) > len(base):
                asset = symbol[:-len(base)]
                return f"{asset}-{base}"
        
        # Si no encuentra una moneda base conocida, devuelve el símbolo original
        return symbol
