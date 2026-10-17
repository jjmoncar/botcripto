"""
Módulo para obtener datos de mercado desde exchanges
"""

import aiohttp
import asyncio
import logging
import ssl
import certifi
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        self.binance_base_url = "https://fapi.binance.com/fapi/v1"
        self.session = None
        
    async def get_session(self):
        """Obtiene o crea una sesión HTTP con soporte SSL robusto"""
        if self.session is None or self.session.closed:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=20, connect=10)
            self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self.session
    
    async def close_session(self):
        """Cierra la sesión HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()
            # Breve pausa para permitir que el loop de eventos cierre los sockets SSL
            await asyncio.sleep(0.25)
    
    async def get_market_data(self, symbol: str, interval: str = '1h', limit: int = 100) -> Optional[Dict]:
        """
        Obtiene datos de mercado para un símbolo específico
        
        Args:
            symbol: Par de trading (ej: BTCUSDT)
            interval: Intervalo de tiempo (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Número de velas a obtener
            
        Returns:
            Dict con datos de mercado o None si hay error
        """
        try:
            session = await self.get_session()
            
            # Obtener datos de velas (klines)
            klines_url = f"{self.binance_base_url}/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            async with session.get(klines_url, params=params) as response:
                if response.status != 200:
                    formatted_symbol = Config.format_trading_pair(symbol)
                    logger.error(f"Error obteniendo datos para {formatted_symbol}: {response.status}")
                    return None
                
                klines_data = await response.json()
                
            if not klines_data or not isinstance(klines_data, list):
                formatted_symbol = Config.format_trading_pair(symbol)
                logger.warning(f"Respuesta vacía o inválida de klines para {formatted_symbol}")
                return None
            
            # Obtener precio actual (con fallback al cierre de la última vela)
            current_price = None
            try:
                ticker_url = f"{self.binance_base_url}/ticker/price"
                ticker_params = {'symbol': symbol}
                
                async with session.get(ticker_url, params=ticker_params) as response:
                    if response.status == 200:
                        ticker_data = await response.json()
                        current_price = float(ticker_data['price'])
            except Exception as te:
                logger.debug(f"No se pudo consultar ticker/price para {symbol}, usando vela: {te}")
            
            # Si el ticker falló, usar el precio de cierre de la última vela
            if current_price is None or current_price <= 0:
                current_price = float(klines_data[-1][4])
            
            # Procesar datos
            df = self._process_klines_data(klines_data)
            if df.empty:
                return None
            
            return {
                'symbol': symbol,
                'interval': interval,
                'current_price': current_price,
                'data': df,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            formatted_symbol = Config.format_trading_pair(symbol)
            logger.error(f"Excepción obteniendo datos para {formatted_symbol}: {e}")
            return None
    
    def _process_klines_data(self, klines_data: List) -> pd.DataFrame:
        """
        Procesa los datos de velas de Binance
        
        Args:
            klines_data: Datos raw de klines de Binance
            
        Returns:
            DataFrame con datos procesados
        """
        if not klines_data:
            return pd.DataFrame()
        columns = [
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ]
        
        df = pd.DataFrame(klines_data, columns=columns)
        
        # Convertir a tipos numéricos apropiados
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convertir timestamp a datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        return df[numeric_columns]
    
    async def get_multiple_timeframes(self, symbol: str, timeframes: List[str]) -> Dict[str, Optional[Dict]]:
        """
        Obtiene datos para múltiples timeframes
        
        Args:
            symbol: Par de trading
            timeframes: Lista de timeframes
            
        Returns:
            Dict con datos para cada timeframe
        """
        tasks = []
        for tf in timeframes:
            task = self.get_market_data(symbol, tf)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        timeframe_data = {}
        for i, tf in enumerate(timeframes):
            if isinstance(results[i], Exception):
                formatted_symbol = Config.format_trading_pair(symbol)
                logger.error(f"Error obteniendo datos para {formatted_symbol} {tf}: {results[i]}")
                timeframe_data[tf] = None
            else:
                timeframe_data[tf] = results[i]
        
        return timeframe_data
    
    async def get_24h_stats(self, symbol: str) -> Optional[Dict]:
        """
        Obtiene estadísticas de 24h para un símbolo
        
        Args:
            symbol: Par de trading
            
        Returns:
            Dict con estadísticas de 24h
        """
        try:
            session = await self.get_session()
            url = f"{self.binance_base_url}/ticker/24hr"
            params = {'symbol': symbol}
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    formatted_symbol = Config.format_trading_pair(symbol)
                    logger.error(f"Error obteniendo stats 24h para {formatted_symbol}: {response.status}")
                    return None
                
                data = await response.json()
                
                return {
                    'symbol': data['symbol'],
                    'price_change': float(data['priceChange']),
                    'price_change_percent': float(data['priceChangePercent']),
                    'high_price': float(data['highPrice']),
                    'low_price': float(data['lowPrice']),
                    'volume': float(data['volume']),
                    'count': int(data['count'])
                }
                
        except Exception as e:
            formatted_symbol = Config.format_trading_pair(symbol)
            logger.error(f"Excepción obteniendo stats 24h para {formatted_symbol}: {e}")
            return None
