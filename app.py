from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal, Optional, Dict, Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from trading_bot.data import fetch_klines
from trading_bot.backtester import backtest, summarize_trades
from trading_bot.strategies import STRATEGY_REGISTRY
from trading_bot.execution.live_trader import LiveTrader
from trading_bot.config import load_binance_config

logger = logging.getLogger("trading_bot")
BASE_DIR = Path(__file__).parent


class BacktestRequest(BaseModel):
    symbol: str
    interval: str
    start: str
    end: str
    strategy: Literal["sma_crossover", "bbands"]
    source: Literal["binance", "yahoo"] = "binance"
    initial_capital: float = 1000.0
    fee: float = 0.001
    # Strategy params
    fast: Optional[int] = 10
    slow: Optional[int] = 30
    window: Optional[int] = 20
    num_std: Optional[float] = 2.0


class LiveSignalRequest(BaseModel):
    symbol: str
    interval: str
    strategy: Literal["sma_crossover", "bbands"]
    source: Literal["binance", "yahoo"] = "binance"
    lookback_days: int = 14
    fast: Optional[int] = 10
    slow: Optional[int] = 30
    window: Optional[int] = 20
    num_std: Optional[float] = 2.0


class LiveOrderRequest(LiveSignalRequest):
    quote_qty: float = Field(..., gt=0)
    testnet: bool = False


def build_strategy(name: str, params: Dict[str, Any]):
    StrategyCls = STRATEGY_REGISTRY[name]
    return StrategyCls(params=params)


def dataframe_to_series_payload(series: pd.Series) -> Dict[str, Any]:
    s = series.dropna()
    return {
        "timestamps": [ts.isoformat() for ts in s.index.to_pydatetime()],
        "values": [float(x) for x in s.to_list()],
    }


app = FastAPI(title="Trading Bot UI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/strategies")
def get_strategies():
    return {
        "strategies": list(STRATEGY_REGISTRY.keys()),
        "params": {
            "sma_crossover": {"fast": 10, "slow": 30},
            "bbands": {"window": 20, "num_std": 2.0},
        },
    }


@app.post("/api/backtest")
def api_backtest(req: BacktestRequest):
    try:
        df = fetch_klines(req.symbol, req.interval, req.start, req.end, source=req.source)
        strat = build_strategy(req.strategy, {
            "fast": req.fast,
            "slow": req.slow,
            "window": req.window,
            "num_std": req.num_std,
        })
        position = strat.generate_position(df)
        result = backtest(
            df=df,
            position=position,
            initial_capital=req.initial_capital,
            fee_rate=req.fee,
        )
        trades = summarize_trades(position, result.returns, fee_rate=req.fee)
        payload = {
            "metrics": result.metrics | trades,
            "equity": dataframe_to_series_payload(result.equity),
            "close": dataframe_to_series_payload(df["close"]),
        }
        return payload
    except Exception as e:
        logger.error("Error performing backtest: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="An error occurred while processing the backtest request")


@app.post("/api/live/signal")
def api_live_signal(req: LiveSignalRequest):
    try:
        end = pd.Timestamp.utcnow()
        start = end - pd.Timedelta(days=req.lookback_days)
        df = fetch_klines(req.symbol, req.interval, start, end, source=req.source)
        strat = build_strategy(req.strategy, {
            "fast": req.fast,
            "slow": req.slow,
            "window": req.window,
            "num_std": req.num_std,
        })
        position = strat.generate_position(df)
        latest_pos = int(position.iloc[-1])
        return {"latest_position": latest_pos}
    except Exception as e:
        logger.error("Error generating live signal: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="An error occurred while fetching live signals")


@app.post("/api/live/order")
def api_live_order(req: LiveOrderRequest):
    try:
        # Compute latest signal from chosen source & interval
        end = pd.Timestamp.utcnow()
        start = end - pd.Timedelta(days=req.lookback_days)
        df = fetch_klines(req.symbol, req.interval, start, end, source=req.source)
        strat = build_strategy(req.strategy, {
            "fast": req.fast,
            "slow": req.slow,
            "window": req.window,
            "num_std": req.num_std,
        })
        position = strat.generate_position(df)
        latest_pos = int(position.iloc[-1])

        # Place order via Binance
        config = load_binance_config(testnet=req.testnet)
        trader = LiveTrader(config=config, symbol=req.symbol, testnet=req.testnet)
        order = trader.run_once_from_signal(latest_position=latest_pos, quote_qty=req.quote_qty)
        return {"latest_position": latest_pos, "order": order}
    except Exception as e:
        logger.error("Error executing live order: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="An error occurred while placing live order")


# Serve static UI after API routes so API paths take precedence
app.mount("/", StaticFiles(directory=str(BASE_DIR / "web"), html=True), name="web")