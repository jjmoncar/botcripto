# 🤖 Bot de Trading de Futuros

Bot automatizado de trading que analiza el mercado de criptomonedas y envía señales de trading a través de Telegram con indicadores técnicos y probabilidades de éxito.

## 🚀 Características

- **Modalidad Híbrida / Dual**: Soporta **Scalping** (operaciones rápidas en 5m/15m) y **Swing** (tendenciales en 1h/4h).
- **Estrategias Técnicas Especializadas**:
  - **Scalping**: Cruces rápidos de EMA 9 / EMA 21, rebotes en Bandas de Bollinger, RSI reactivo, cruces de Estocástico y picos de volumen.
  - **Swing**: Análisis tendencial con EMA 20/50, MACD y fuerza de tendencia ADX.
- **Notificaciones Diferenciadas vía Telegram**: Alertas visuales con formato específico para Scalping (⚡ con TP1 y TP Final) o Swing (📈).
- **Niveles Dinámicos de Riesgo**: Stop Loss y Take Profit adaptados con ATR o porcentajes ajustables.
- **Múltiples pares de trading**: Monitoreo de 12 pares principales en Binance Futures.
- **Protección contra duplicados**: Cooldown inteligente e independiente para Scalping y Swing.

## 📋 Requisitos

- Python 3.8+
- Cuenta de Telegram y bot token
- Conexión a internet

## 🛠️ Instalación

1. **Clona o descarga** el proyecto
2. **Instala las dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura las variables de entorno**:
   - Copia `.env.example` a `.env`
   - Completa con tus datos de Telegram

## ⚙️ Configuración

### Bot de Telegram

1. **Crea un bot**:
   - Habla con [@BotFather](https://t.me/botfather) en Telegram
   - Usa `/newbot` y sigue las instrucciones
   - Guarda el token que te proporciona

2. **Obtén tu Chat ID**:
   - Envía un mensaje a tu bot
   - Visita: `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
   - Busca el `chat.id` en la respuesta

3. **Actualiza el archivo `.env`**:
   ```
   TELEGRAM_BOT_TOKEN=tu_token_aqui
   TELEGRAM_CHAT_ID=tu_chat_id_aqui
   ```

## 🚀 Uso

Ejecuta el bot:
```bash
python main.py
```

El bot comenzará a monitorear los mercados y enviará notificaciones cuando detecte señales de trading.

## 📊 Indicadores Utilizados

- **RSI (14)**: Identifica condiciones de sobrecompra/sobreventa
- **MACD (12,26,9)**: Detecta cambios de momentum
- **Bollinger Bands (20,2)**: Identifica volatilidad y niveles extremos
- **EMA (20,50)**: Confirma tendencias
- **Stochastic (14,3,3)**: Oscilador de momentum
- **ADX (14)**: Mide la fuerza de la tendencia
- **Volumen**: Confirma la validez de las señales

## 📈 Pares Monitoreados

Por defecto, el bot monitorea los siguientes contratos en Binance Futures:
- BTCUSDT
- ETHUSDT
- ADAUSDT
- SOLUSDT
- DOTUSDT
- LINKUSDT
- AVAXUSDT
- BNBUSDT
- XRPUSDT
- XLMUSDT
- TRXUSDT
- LTCUSDT

Puedes modificar o ampliar la lista en `config.py`.

## ⚡ Modalidades y Configuración de Riesgo

El bot puede operar en tres modos configurables en `TRADING_MODE`:
1. **`HYBRID` (Por defecto)**: Monitorea tanto temporalidades de Scalping (`5m, 15m`) como de Swing (`1h, 4h`).
2. **`SCALPING`**: Se enfoca exclusivamente en operaciones rápidas (`5m, 15m`).
3. **`SWING`**: Se enfoca exclusivamente en operaciones tendenciales (`1h, 4h`).

### Parámetros de Riesgo:
- **Scalping**:
  - Stop Loss: 0.8% (o 1.2x ATR)
  - Take Profit 1: ~1.0% (o 1.5x ATR)
  - Take Profit Final: ~1.6% (o 2.4x ATR)
  - Probabilidad mínima: 75%
  - Cooldown: 10 minutos
- **Swing**:
  - Stop Loss: 2.0% (o 2.0x ATR)
  - Take Profit: 4.0% (o 4.0x ATR)
  - Probabilidad mínima: 80%
  - Cooldown: 30 minutos

## 📱 Formato de Señales en Telegram

- **Scalping**: Encabezado `⚡ SEÑAL SCALPING (5m)`, niveles de TP1 y TP Final, resumen con EMA 9/21, RSI y Estocástico.
- **Swing**: Encabezado `📊 SEÑAL SWING (1h)`, niveles de TP único y resumen con MACD, ADX y EMA 20/50.

## 🔧 Personalización (.env)

Puedes configurar opciones mediante el archivo `.env`:
- `TRADING_MODE`: `HYBRID`, `SCALPING` o `SWING`
- `SCALPING_TIMEFRAMES`: `5m,15m`
- `SWING_TIMEFRAMES`: `1h,4h`
- `ANALYSIS_INTERVAL`: Intervalo de ciclo en segundos (ej: `60` para scalping/hybrid, `300` para swing)
- `SCALPING_MIN_PROBABILITY`: Probabilidad mínima para enviar alertas de Scalping (ej: `75.0`)
- `SCALPING_STOP_LOSS_PERCENT`: Porcentaje de Stop Loss para Scalping (ej: `0.8`)
- `SCALPING_TAKE_PROFIT_PERCENT`: Porcentaje de Take Profit para Scalping (ej: `1.6`)
- `SCALPING_COOLDOWN_MINUTES`: Cooldown para Scalping en minutos (ej: `10`)
- `MIN_PROBABILITY`: Probabilidad mínima para Swing (ej: `80.0`)
- `SIGNAL_COOLDOWN_MINUTES`: Cooldown para Swing en minutos (ej: `30`)
- `MONETAG_MINI_APP_URL`: Enlace opcional de monetización inline keyboard

## ⚠️ Disclaimer

Este bot es para fines educativos y de investigación. El trading de futuros conlleva riesgos significativos. Siempre:

- Haz tu propia investigación
- No inviertas más de lo que puedes permitirte perder
- Considera consultar con un asesor financiero
- Las señales no garantizan ganancias

## 📝 Logs

El bot genera logs en `trading_bot.log` para monitorear su funcionamiento y depurar problemas.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.
