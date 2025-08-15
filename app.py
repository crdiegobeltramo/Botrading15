from __future__ import annotations

from typing import Literal, Optional, Dict, Any

import os
import base64
import hmac

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.responses import PlainTextResponse

from trading_bot.data import fetch_klines
from trading_bot.backtester import backtest, summarize_trades
from trading_bot.strategies import STRATEGY_REGISTRY
from trading_bot.execution.live_trader import LiveTrader
from trading_bot.config import load_binance_config


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

# Basic Auth middleware (protects API and static files)
_BASIC_USER = os.getenv("BASIC_AUTH_USER")
_BASIC_PASS = os.getenv("BASIC_AUTH_PASS")

@app.middleware("http")
async def basic_auth(request: Request, call_next):
    if not _BASIC_USER or not _BASIC_PASS:
        return await call_next(request)
    auth = request.headers.get("authorization")
    ok = False
    if auth and auth.startswith("Basic "):
        try:
            decoded = base64.b64decode(auth.split(" ", 1)[1]).decode("utf-8")
            user, pw = decoded.split(":", 1)
            if hmac.compare_digest(user, _BASIC_USER) and hmac.compare_digest(pw, _BASIC_PASS):
                ok = True
        except Exception:
            ok = False
    if not ok:
        return PlainTextResponse("Authentication required", status_code=401, headers={"WWW-Authenticate": "Basic realm=\"TradingBot\""})
    return await call_next(request)

# Serve static UI
app.mount("/", StaticFiles(directory="/workspace/web", html=True), name="web")


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
        raise HTTPException(status_code=400, detail=str(e))


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
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/live/order")
def api_live_order(req: LiveOrderRequest):
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

        config = load_binance_config(testnet=req.testnet)
        trader = LiveTrader(config=config, symbol=req.symbol, testnet=req.testnet)
        order = trader.run_once_from_signal(latest_position=latest_pos, quote_qty=req.quote_qty)
        return {"latest_position": latest_pos, "order": order}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))