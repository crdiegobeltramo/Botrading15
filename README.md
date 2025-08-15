# Bot de Trading para Binance con Backtesting (Python)

Este proyecto incluye:
- Descarga de datos OHLCV desde Binance (o Yahoo como alternativa)
- Estrategias: Cruce de Medias Móviles (SMA), Bandas de Bollinger (BB)
- Motor de backtesting con métricas (rentabilidad, Sharpe, drawdown, etc.)
- Modo live (de ejemplo) usando tu API (Soporta Testnet)

## Requisitos

- Python 3.10+
- Instalar dependencias:

```bash
pip install -r requirements.txt --break-system-packages --user
```

## Variables de entorno (para Live Trading)

Exporta tus credenciales (o usa testnet sin claves para endpoints públicos):

```bash
export BINANCE_API_KEY="tu_api_key"
export BINANCE_API_SECRET="tu_api_secret"
```

## Uso

### Backtesting

Binance (si tu red lo permite):

```bash
python3 main.py backtest \
  --symbol BTCUSDT \
  --interval 1h \
  --start 2022-01-01 \
  --end 2023-01-01 \
  --strategy sma_crossover \
  --fast 10 --slow 30 \
  --initial-capital 1000 --fee 0.001
```

Yahoo (alternativa, ejemplo con BTC-USD):

```bash
python3 main.py backtest \
  --symbol BTC-USD \
  --interval 1h \
  --start 2022-01-01 \
  --end 2023-01-01 \
  --strategy bbands \
  --window 20 --num-std 2.0 \
  --initial-capital 1000 --fee 0.001 \
  --source yahoo
```

### Live (demo)

Ejemplo de ejecución (testnet):

```bash
python3 main.py live \
  --symbol BTCUSDT \
  --interval 1h \
  --strategy sma_crossover --fast 10 --slow 30 \
  --testnet --quote-qty 50
```

Notas:
- El modo live incluido es un ejemplo mínimo que toma la última señal y ejecuta una orden de mercado en consecuencia. Amplíalo para orquestación continua (loops, websockets, gestión de riesgos, etc.).
- Para testnet spot, el `base_url` utilizado es `https://testnet.binance.vision`.
- Si tu entorno bloquea Binance, usa `--source yahoo` con símbolos estilo Yahoo (p.ej. `BTC-USD`, `ETH-USD`).

## Estructura

```
trading_bot/
  config.py
  data.py
  backtester.py
  execution/
    live_trader.py
  strategies/
    base.py
    sma_crossover.py
    bbands.py
main.py
```

## Métricas del backtest
- total_return
- cagr
- sharpe
- max_drawdown
- num_trades
- win_rate

## Advertencia
El trading conlleva riesgos. Este software se proporciona con fines educativos y sin garantías. Úsalo bajo tu propia responsabilidad.