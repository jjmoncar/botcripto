"""
Analizador de mercado con indicadores técnicos (sin TA-Lib)
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional, List
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    def __init__(self):
        self.min_data_points = 50  # Mínimo de datos para análisis confiable
        
    def analyze(self, market_data: Dict, symbol: str, timeframe: Optional[str] = None) -> Optional[Dict]:
        """
        Analiza los datos de mercado y genera señales de trading (Scalping o Swing)
        
        Args:
            market_data: Datos de mercado del DataFetcher
            symbol: Par de trading
            timeframe: Temporalidad opcional (si no se especifica, se toma de market_data)
            
        Returns:
            Dict con señal de trading o None
        """
        try:
            df = market_data['data']
            current_price = market_data['current_price']
            tf = timeframe or market_data.get('interval', '1h')
            is_scalping = Config.is_scalping_timeframe(tf)
            
            if len(df) < self.min_data_points:
                formatted_symbol = Config.format_trading_pair(symbol)
                logger.warning(f"Datos insuficientes para {formatted_symbol} ({tf}): {len(df)} puntos")
                return None
            
            # Calcular indicadores técnicos
            indicators = self._calculate_indicators(df)
            
            # Analizar señales según la modalidad (Scalping o Swing)
            signal_analysis = self._analyze_signals(indicators, df, is_scalping=is_scalping)
            
            if not signal_analysis['has_signal']:
                return None
            
            # Calcular probabilidad
            probability = self._calculate_probability(signal_analysis, indicators, is_scalping=is_scalping)
            
            # Calcular niveles de stop loss y take profit (con TP1 y TP2 para scalping)
            stop_loss, take_profit, tp1 = self._calculate_levels(
                current_price, signal_analysis['direction'], indicators, is_scalping=is_scalping
            )
            
            return {
                'symbol': symbol,
                'direction': signal_analysis['direction'],
                'probability': probability,
                'current_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'take_profit_1': tp1,
                'timeframe': tf,
                'mode': 'SCALPING' if is_scalping else 'SWING',
                'indicators_summary': self._format_indicators_summary(indicators, is_scalping=is_scalping),
                'signal_strength': signal_analysis['strength'],
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            formatted_symbol = Config.format_trading_pair(symbol)
            logger.error(f"Error analizando {formatted_symbol}: {e}")
            return None
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calcula todos los indicadores técnicos incluyendo EMAs de Scalping"""
        try:
            close = df['close'].values
            high = df['high'].values
            low = df['low'].values
            volume = df['volume'].values
            
            indicators = {}
            
            # RSI
            rsi = self._calculate_rsi(close, 14)
            indicators['rsi'] = rsi
            indicators['rsi_current'] = rsi[-1] if len(rsi) > 0 else 50.0
            
            # MACD
            macd, macd_signal, macd_hist = self._calculate_macd(close, 12, 26, 9)
            indicators['macd'] = macd
            indicators['macd_signal'] = macd_signal
            indicators['macd_histogram'] = macd_hist
            indicators['macd_current'] = macd[-1] if len(macd) > 0 else 0.0
            indicators['macd_signal_current'] = macd_signal[-1] if len(macd_signal) > 0 else 0.0
            indicators['macd_hist_current'] = macd_hist[-1] if len(macd_hist) > 0 else 0.0
            
            # Bandas de Bollinger
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(close, 20, 2)
            indicators['bb_upper'] = bb_upper
            indicators['bb_middle'] = bb_middle
            indicators['bb_lower'] = bb_lower
            indicators['bb_upper_current'] = bb_upper[-1] if len(bb_upper) > 0 else close[-1]
            indicators['bb_lower_current'] = bb_lower[-1] if len(bb_lower) > 0 else close[-1]
            indicators['bb_middle_current'] = bb_middle[-1] if len(bb_middle) > 0 else close[-1]
            
            # Medias móviles rápidas para Scalping (EMA 9 y EMA 21)
            ema_9 = self._calculate_ema(close, getattr(Config, 'EMA_FAST_SCALPING', 9))
            ema_21 = self._calculate_ema(close, getattr(Config, 'EMA_SLOW_SCALPING', 21))
            indicators['ema_9'] = ema_9
            indicators['ema_21'] = ema_21
            indicators['ema_9_current'] = ema_9[-1] if len(ema_9) > 0 else close[-1]
            indicators['ema_21_current'] = ema_21[-1] if len(ema_21) > 0 else close[-1]
            indicators['ema_9_prev'] = ema_9[-2] if len(ema_9) > 1 else ema_9[-1]
            indicators['ema_21_prev'] = ema_21[-2] if len(ema_21) > 1 else ema_21[-1]
            
            # Medias móviles estándar (EMA 20 y EMA 50)
            ema_20 = self._calculate_ema(close, 20)
            ema_50 = self._calculate_ema(close, 50)
            indicators['ema_20'] = ema_20
            indicators['ema_50'] = ema_50
            indicators['ema_20_current'] = ema_20[-1] if len(ema_20) > 0 else close[-1]
            indicators['ema_50_current'] = ema_50[-1] if len(ema_50) > 0 else close[-1]
            
            # Stochastic
            stoch_k, stoch_d = self._calculate_stochastic(high, low, close, 14, 3)
            indicators['stoch_k'] = stoch_k
            indicators['stoch_d'] = stoch_d
            indicators['stoch_k_current'] = stoch_k[-1] if len(stoch_k) > 0 else 50.0
            indicators['stoch_d_current'] = stoch_d[-1] if len(stoch_d) > 0 else 50.0
            indicators['stoch_k_prev'] = stoch_k[-2] if len(stoch_k) > 1 else stoch_k[-1]
            indicators['stoch_d_prev'] = stoch_d[-2] if len(stoch_d) > 1 else stoch_d[-1]
            
            # ADX (Average Directional Index)
            adx = self._calculate_adx(high, low, close, 14)
            indicators['adx'] = adx
            indicators['adx_current'] = adx[-1] if len(adx) > 0 else 25.0
            
            # Volume indicators
            volume_sma = self._calculate_sma(volume, 20)
            indicators['volume_sma'] = volume_sma
            indicators['volume_ratio'] = volume[-1] / volume_sma[-1] if len(volume_sma) > 0 and volume_sma[-1] > 0 else 1.0
            
            # ATR (Average True Range)
            atr = self._calculate_atr(high, low, close, 14)
            indicators['atr'] = atr
            indicators['atr_current'] = atr[-1] if len(atr) > 0 else 0.0
            
            # Precio actual vs medias
            current_price = close[-1]
            indicators['price_vs_ema20'] = (current_price - indicators['ema_20_current']) / indicators['ema_20_current'] * 100
            indicators['price_vs_ema50'] = (current_price - indicators['ema_50_current']) / indicators['ema_50_current'] * 100
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculando indicadores: {e}")
            return {}
    
    def _calculate_rsi(self, prices, period=14):
        """Calcula el RSI (Relative Strength Index) usando el suavizado de Wilder"""
        try:
            series = pd.Series(prices)
            delta = series.diff()
            gain = delta.clip(lower=0.0)
            loss = -delta.clip(upper=0.0)
            
            avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
            avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
            
            rs = avg_gain / avg_loss.replace(0, np.nan)
            rsi = 100.0 - (100.0 / (1.0 + rs))
            
            # Casos especiales: sin pérdidas -> 100, sin ganancias -> 0, sin cambios -> 50
            rsi = rsi.where(avg_loss != 0, 100.0)
            rsi = rsi.where(~((avg_gain == 0) & (avg_loss == 0)), 50.0)
            
            return rsi.fillna(50.0).values
        except Exception as e:
            logger.error(f"Error en RSI: {e}")
            return np.full(len(prices), 50.0)
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calcula MACD"""
        try:
            ema_fast = self._calculate_ema(prices, fast)
            ema_slow = self._calculate_ema(prices, slow)
            
            macd_line = ema_fast - ema_slow
            signal_line = self._calculate_ema(macd_line, signal)
            histogram = macd_line - signal_line
            
            return macd_line, signal_line, histogram
        except Exception as e:
            logger.error(f"Error en MACD: {e}")
            return np.zeros(len(prices)), np.zeros(len(prices)), np.zeros(len(prices))
    
    def _calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Calcula Bandas de Bollinger"""
        try:
            sma = self._calculate_sma(prices, period)
            std = pd.Series(prices).rolling(window=period, min_periods=1).std().fillna(0.0).values
            
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            return upper_band, sma, lower_band
        except Exception as e:
            logger.error(f"Error en Bollinger Bands: {e}")
            return np.full(len(prices), prices[-1]), np.full(len(prices), prices[-1]), np.full(len(prices), prices[-1])
    
    def _calculate_ema(self, prices, period):
        """Calcula EMA (Exponential Moving Average) estándar"""
        try:
            return pd.Series(prices).ewm(span=period, adjust=False).mean().fillna(prices[0]).values
        except Exception as e:
            logger.error(f"Error en EMA: {e}")
            return np.full(len(prices), prices[-1])
    
    def _calculate_sma(self, prices, period):
        """Calcula SMA (Simple Moving Average)"""
        try:
            return pd.Series(prices).rolling(window=period, min_periods=1).mean().fillna(prices[0]).values
        except Exception as e:
            logger.error(f"Error en SMA: {e}")
            return np.full(len(prices), prices[-1])
    
    def _calculate_stochastic(self, high, low, close, k_period=14, d_period=3):
        """Calcula Stochastic Oscillator"""
        try:
            lowest_low = pd.Series(low).rolling(window=k_period, min_periods=1).min()
            highest_high = pd.Series(high).rolling(window=k_period, min_periods=1).max()
            
            diff = highest_high - lowest_low
            k_percent = 100.0 * ((pd.Series(close) - lowest_low) / diff.replace(0, np.nan))
            k_percent = k_percent.replace([np.inf, -np.inf], 50.0).fillna(50.0)
            
            d_percent = k_percent.rolling(window=d_period, min_periods=1).mean().fillna(50.0)
            
            return k_percent.values, d_percent.values
        except Exception as e:
            logger.error(f"Error en Stochastic: {e}")
            return np.full(len(close), 50.0), np.full(len(close), 50.0)
    
    def _calculate_atr(self, high, low, close, period=14):
        """Calcula el ATR (Average True Range)"""
        try:
            high_series = pd.Series(high)
            low_series = pd.Series(low)
            close_series = pd.Series(close)
            
            tr1 = high_series - low_series
            tr2 = abs(high_series - close_series.shift())
            tr3 = abs(low_series - close_series.shift())
            
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = true_range.ewm(com=period - 1, min_periods=1).mean()
            
            return atr.values
        except Exception as e:
            logger.error(f"Error en ATR: {e}")
            return np.zeros(len(close))

    def _calculate_adx(self, high, low, close, period=14):
        """Calcula ADX (Average Directional Index) con corrección matemática"""
        try:
            atr = self._calculate_atr(high, low, close, period)
            
            high_diff = np.diff(high)
            low_diff = -np.diff(low)
            
            dm_plus = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0.0)
            dm_minus = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0.0)
            
            # Smooth DMs con media móvil
            dm_plus_smooth = pd.Series(dm_plus).rolling(window=period, min_periods=1).mean()
            dm_minus_smooth = pd.Series(dm_minus).rolling(window=period, min_periods=1).mean()
            
            atr_series = pd.Series(atr[1:]).replace(0, np.nan)
            di_plus = (100.0 * (dm_plus_smooth / atr_series)).fillna(0.0)
            di_minus = (100.0 * (dm_minus_smooth / atr_series)).fillna(0.0)
            
            di_sum = di_plus + di_minus
            dx = (100.0 * (abs(di_plus - di_minus) / di_sum.replace(0, np.nan))).fillna(0.0)
            adx = dx.rolling(window=period, min_periods=1).mean().fillna(25.0)
            
            # Mantener la misma longitud de la serie de velas
            return np.concatenate([[25.0], adx.values])
        except Exception as e:
            logger.error(f"Error en ADX: {e}")
            return np.full(len(close), 25.0)
            
    def _analyze_signals(self, indicators: Dict, df: pd.DataFrame, is_scalping: bool = False) -> Dict:
        """Analiza las señales basadas en los indicadores para Scalping o Swing"""
        signals = {
            'bullish': 0,
            'bearish': 0,
            'strength': 0,
            'has_signal': False,
            'direction': None
        }
        
        try:
            current_price = df['close'].iloc[-1]
            
            if is_scalping:
                # ================= ESTRATEGIA DE SCALPING RÁPIDO =================
                # 1. EMAs rápidas (Estrategia de cruce y tendencia EMA 9 / EMA 21)
                ema_9 = indicators.get('ema_9_current', current_price)
                ema_21 = indicators.get('ema_21_current', current_price)
                ema_9_prev = indicators.get('ema_9_prev', ema_9)
                ema_21_prev = indicators.get('ema_21_prev', ema_21)
                
                # Cruce reciente de EMAs
                if ema_9 > ema_21 and ema_9_prev <= ema_21_prev:
                    signals['bullish'] += 3  # Cruce dorado de scalping
                elif ema_9 < ema_21 and ema_9_prev >= ema_21_prev:
                    signals['bearish'] += 3  # Cruce de muerte de scalping
                elif ema_9 > ema_21 and current_price > ema_9:
                    signals['bullish'] += 2
                elif ema_9 < ema_21 and current_price < ema_9:
                    signals['bearish'] += 2
                
                # 2. Bandas de Bollinger para rebotes de scalping
                if current_price <= indicators['bb_lower_current']:
                    signals['bullish'] += 2
                elif current_price >= indicators['bb_upper_current']:
                    signals['bearish'] += 2
                
                # 3. RSI rápido para Scalping
                rsi = indicators['rsi_current']
                if rsi < 35:
                    signals['bullish'] += 2
                elif rsi > 65:
                    signals['bearish'] += 2
                
                # 4. Stochastic rápido (cruces K y D)
                k = indicators['stoch_k_current']
                d = indicators['stoch_d_current']
                k_prev = indicators.get('stoch_k_prev', k)
                d_prev = indicators.get('stoch_d_prev', d)
                
                if k < 25 and k > d and k_prev <= d_prev:
                    signals['bullish'] += 2  # Cruce alcista en sobreventa
                elif k > 75 and k < d and k_prev >= d_prev:
                    signals['bearish'] += 2  # Cruce bajista en sobrecompra
                elif k < 20 and d < 20:
                    signals['bullish'] += 1
                elif k > 80 and d > 80:
                    signals['bearish'] += 1
                
                # 5. MACD Histograma rápido
                if indicators['macd_hist_current'] > 0 and indicators['macd_current'] > indicators['macd_signal_current']:
                    signals['bullish'] += 1
                elif indicators['macd_hist_current'] < 0 and indicators['macd_current'] < indicators['macd_signal_current']:
                    signals['bearish'] += 1
                
                # 6. Volumen (Confirmación obligatoria para scalping)
                if indicators['volume_ratio'] > 1.8:
                    if signals['bullish'] > signals['bearish']:
                        signals['bullish'] += 2
                    else:
                        signals['bearish'] += 2
                elif indicators['volume_ratio'] > 1.3:
                    if signals['bullish'] > signals['bearish']:
                        signals['bullish'] += 1
                    else:
                        signals['bearish'] += 1
                
                # Umbral de activación para scalping (más ágil)
                signal_diff = abs(signals['bullish'] - signals['bearish'])
                total_signals = signals['bullish'] + signals['bearish']
                
                if signal_diff >= 3 and total_signals >= 4:
                    signals['has_signal'] = True
                    signals['direction'] = 'LONG' if signals['bullish'] > signals['bearish'] else 'SHORT'
                    signals['strength'] = signal_diff
            
            else:
                # ================= ESTRATEGIA SWING / TENDENCIAL =================
                # Análisis RSI
                rsi = indicators['rsi_current']
                if rsi < 30:  # Sobreventa
                    signals['bullish'] += 2
                elif rsi < 40:
                    signals['bullish'] += 1
                elif rsi > 70:  # Sobrecompra
                    signals['bearish'] += 2
                elif rsi > 60:
                    signals['bearish'] += 1
                
                # Análisis MACD
                if indicators['macd_current'] > indicators['macd_signal_current']:
                    if indicators['macd_hist_current'] > 0:
                        signals['bullish'] += 2
                    else:
                        signals['bullish'] += 1
                else:
                    if indicators['macd_hist_current'] < 0:
                        signals['bearish'] += 2
                    else:
                        signals['bearish'] += 1
                
                # Análisis Bandas de Bollinger
                if current_price <= indicators['bb_lower_current']:
                    signals['bullish'] += 2
                elif current_price >= indicators['bb_upper_current']:
                    signals['bearish'] += 2
                
                # Análisis EMAs 20 y 50
                if indicators['ema_20_current'] > indicators['ema_50_current']:
                    signals['bullish'] += 1
                else:
                    signals['bearish'] += 1
                
                if current_price > indicators['ema_20_current']:
                    signals['bullish'] += 1
                else:
                    signals['bearish'] += 1
                
                # Análisis Stochastic
                if indicators['stoch_k_current'] < 20 and indicators['stoch_d_current'] < 20:
                    signals['bullish'] += 1
                elif indicators['stoch_k_current'] > 80 and indicators['stoch_d_current'] > 80:
                    signals['bearish'] += 1
                
                # ADX para confirmar fuerza de tendencia
                if indicators['adx_current'] > 25:
                    if signals['bullish'] > signals['bearish']:
                        signals['bullish'] += 1
                    else:
                        signals['bearish'] += 1
                
                # Volumen
                if indicators['volume_ratio'] > 1.5:
                    if signals['bullish'] > signals['bearish']:
                        signals['bullish'] += 1
                    else:
                        signals['bearish'] += 1
                
                # Determinar señal final Swing
                signal_diff = abs(signals['bullish'] - signals['bearish'])
                total_signals = signals['bullish'] + signals['bearish']
                
                if signal_diff >= 3 and total_signals >= 5:
                    signals['has_signal'] = True
                    signals['direction'] = 'LONG' if signals['bullish'] > signals['bearish'] else 'SHORT'
                    signals['strength'] = signal_diff
            
            return signals
            
        except Exception as e:
            logger.error(f"Error analizando señales: {e}")
            return signals
    
    def _calculate_probability(self, signal_analysis: Dict, indicators: Dict, is_scalping: bool = False) -> float:
        """Calcula la probabilidad de éxito de la señal ajustada a Scalping o Swing"""
        try:
            base_probability = 50.0
            
            # Ajustar por fuerza de la señal
            multiplier = 6 if is_scalping else 5
            strength_bonus = min(signal_analysis['strength'] * multiplier, 25)
            base_probability += strength_bonus
            
            # Ajustar por RSI
            rsi = indicators['rsi_current']
            threshold_low = 35 if is_scalping else 30
            threshold_high = 65 if is_scalping else 70
            
            if signal_analysis['direction'] == 'LONG':
                if rsi < threshold_low:
                    base_probability += 10
                elif rsi < threshold_low + 10:
                    base_probability += 5
            else:  # SHORT
                if rsi > threshold_high:
                    base_probability += 10
                elif rsi > threshold_high - 10:
                    base_probability += 5
            
            # Ajustar por alineación de EMAs
            if is_scalping:
                ema_9 = indicators.get('ema_9_current', 0)
                ema_21 = indicators.get('ema_21_current', 0)
                if signal_analysis['direction'] == 'LONG' and ema_9 > ema_21:
                    base_probability += 8
                elif signal_analysis['direction'] == 'SHORT' and ema_9 < ema_21:
                    base_probability += 8
            else:
                if signal_analysis['direction'] == 'LONG' and indicators['ema_20_current'] > indicators['ema_50_current']:
                    base_probability += 5
                elif signal_analysis['direction'] == 'SHORT' and indicators['ema_20_current'] < indicators['ema_50_current']:
                    base_probability += 5
                    
                # Ajustar por ADX (tendencia en Swing)
                adx = indicators['adx_current']
                if adx > 35:
                    base_probability += 10
                elif adx > 25:
                    base_probability += 5
            
            # Ajustar por volumen
            if indicators['volume_ratio'] > 1.8:
                base_probability += 8 if is_scalping else 5
            elif indicators['volume_ratio'] > 1.3:
                base_probability += 4
            
            # Limitar probabilidad entre 50% y 95%
            return min(max(base_probability, 50.0), 95.0)
            
        except Exception as e:
            logger.error(f"Error calculando probabilidad: {e}")
            return 50.0
    
    def _calculate_levels(self, current_price: float, direction: str, indicators: Dict = None, is_scalping: bool = False) -> tuple:
        """
        Calcula niveles de Stop Loss y Take Profit adaptados a Scalping o Swing
        
        Returns:
            tuple: (stop_loss, take_profit_final, take_profit_1)
        """
        try:
            if is_scalping:
                sl_pct = getattr(Config, 'SCALPING_STOP_LOSS_PERCENT', 0.8) / 100.0
                tp_pct = getattr(Config, 'SCALPING_TAKE_PROFIT_PERCENT', 1.6) / 100.0
                tp1_pct = tp_pct * 0.6  # TP1 al ~60% del recorrido total
                
                atr = indicators.get('atr_current', 0) if indicators else 0
                
                # En scalping se usa un multiplicador ATR más ceñido (1.2 para SL, 1.5 para TP1, 2.4 para TP2)
                if atr and (0.0005 * current_price <= atr <= current_price * 0.05):
                    if direction == 'LONG':
                        stop_loss = current_price - (atr * 1.2)
                        tp1 = current_price + (atr * 1.5)
                        take_profit = current_price + (atr * 2.4)
                    else:  # SHORT
                        stop_loss = current_price + (atr * 1.2)
                        tp1 = current_price - (atr * 1.5)
                        take_profit = current_price - (atr * 2.4)
                else:
                    if direction == 'LONG':
                        stop_loss = current_price * (1.0 - sl_pct)
                        tp1 = current_price * (1.0 + tp1_pct)
                        take_profit = current_price * (1.0 + tp_pct)
                    else:  # SHORT
                        stop_loss = current_price * (1.0 + sl_pct)
                        tp1 = current_price * (1.0 - tp1_pct)
                        take_profit = current_price * (1.0 - tp_pct)
            else:
                sl_pct = getattr(Config, 'STOP_LOSS_PERCENT', 2.0) / 100.0
                tp_pct = getattr(Config, 'TAKE_PROFIT_PERCENT', 4.0) / 100.0
                tp1_pct = tp_pct * 0.6
                
                atr = indicators.get('atr_current', 0) if indicators else 0
                
                if atr and (0.001 * current_price <= atr <= current_price * 0.1):
                    if direction == 'LONG':
                        stop_loss = current_price - (atr * 2.0)
                        tp1 = current_price + (atr * 2.5)
                        take_profit = current_price + (atr * 4.0)
                    else:  # SHORT
                        stop_loss = current_price + (atr * 2.0)
                        tp1 = current_price - (atr * 2.5)
                        take_profit = current_price - (atr * 4.0)
                else:
                    if direction == 'LONG':
                        stop_loss = current_price * (1.0 - sl_pct)
                        tp1 = current_price * (1.0 + tp1_pct)
                        take_profit = current_price * (1.0 + tp_pct)
                    else:  # SHORT
                        stop_loss = current_price * (1.0 + sl_pct)
                        tp1 = current_price * (1.0 - tp1_pct)
                        take_profit = current_price * (1.0 - tp_pct)
            
            # Garantizar que los niveles sean positivos
            stop_loss = max(stop_loss, current_price * 0.001)
            take_profit = max(take_profit, current_price * 0.001)
            tp1 = max(tp1, current_price * 0.001)
            
            return stop_loss, take_profit, tp1
            
        except Exception as e:
            logger.error(f"Error calculando niveles: {e}")
            sl_pct = (0.8 if is_scalping else 2.0) / 100.0
            tp_pct = (1.6 if is_scalping else 4.0) / 100.0
            if direction == 'LONG':
                return current_price * (1.0 - sl_pct), current_price * (1.0 + tp_pct), current_price * (1.0 + tp_pct * 0.6)
            else:
                return current_price * (1.0 + sl_pct), max(current_price * (1.0 - tp_pct), current_price * 0.001), max(current_price * (1.0 - tp_pct * 0.6), current_price * 0.001)
    
    def _format_indicators_summary(self, indicators: Dict, is_scalping: bool = False) -> str:
        """Formatea un resumen visual de los indicadores para Scalping o Swing"""
        try:
            if is_scalping:
                summary = f"""
• EMA 9/21: {indicators.get('ema_9_current', 0):.4f} / {indicators.get('ema_21_current', 0):.4f}
• RSI (14): {indicators['rsi_current']:.1f}
• Stoch K/D: {indicators['stoch_k_current']:.1f} / {indicators['stoch_d_current']:.1f}
• Vol Ratio: {indicators['volume_ratio']:.2f}x
• ATR (volatilidad): ${indicators['atr_current']:.4f}
                """.strip()
            else:
                summary = f"""
• RSI: {indicators['rsi_current']:.1f}
• MACD: {indicators['macd_current']:.6f}
• ADX: {indicators['adx_current']:.1f}
• Stoch: {indicators['stoch_k_current']:.1f}
• Vol Ratio: {indicators['volume_ratio']:.2f}x
                """.strip()
            
            return summary
            
        except Exception as e:
            logger.error(f"Error formateando resumen: {e}")
            return "Error en indicadores"
