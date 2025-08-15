from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import numpy as np
import pandas as pd
from binance.spot import Spot as SpotClient

try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None


_BINANCE_INTERVAL_MS = {
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "2h": 7_200_000,
    "4h": 14_400_000,
    "6h": 21_600_000,
    "8h": 28_800_000,
    "12h": 43_200_000,
    "1d": 86_400_000,
    "3d": 259_200_000,
    "1w": 604_800_000,
    "1M": 2_592_000_000,  # aprox 30d
}


def _to_millis(dt: str | datetime) -> int:
    if isinstance(dt, str):
        ts = pd.Timestamp(dt, tz="UTC")
    elif isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ts = pd.Timestamp(dt)
    else:
        raise TypeError("dt must be str or datetime")
    return int(ts.timestamp() * 1000)


def _infer_periods_per_year(interval: str) -> float:
    seconds = _BINANCE_INTERVAL_MS[interval] / 1000
    return (365 * 24 * 3600) / seconds


def fetch_klines_binance(
    symbol: str,
    interval: str,
    start: str | datetime,
    end: str | datetime,
    limit: int = 1000,
) -> pd.DataFrame:
    if interval not in _BINANCE_INTERVAL_MS:
        raise ValueError(f"Intervalo no soportado: {interval}")

    start_ms = _to_millis(start)
    end_ms = _to_millis(end)

    client = SpotClient()

    all_rows: List[List] = []
    fetch_start = start_ms
    interval_ms = _BINANCE_INTERVAL_MS[interval]

    while True:
        batch = client.klines(
            symbol=symbol,
            interval=interval,
            startTime=fetch_start,
            endTime=end_ms,
            limit=limit,
        )
        if not batch:
            break
        all_rows.extend(batch)
        last_open_time = batch[-1][0]
        next_start = last_open_time + interval_ms
        if next_start > end_ms or len(batch) < limit:
            break
        fetch_start = next_start

    if not all_rows:
        raise RuntimeError("No se obtuvieron velas; verifica símbolo/intervalo/fechas")

    cols = [
        "open_time","open","high","low","close","volume",
        "close_time","quote_volume","trades","taker_base","taker_quote","ignore"
    ]
    df = pd.DataFrame(all_rows, columns=cols)
    for c in ["open","high","low","close","volume","quote_volume","taker_base","taker_quote"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
    df = df.set_index("close_time").sort_index()

    df = df[~df.index.duplicated(keep="last")]

    df.attrs["interval"] = interval
    df.attrs["periods_per_year"] = _infer_periods_per_year(interval)

    return df[["open","high","low","close","volume"]]


def _yahoo_interval_map(interval: str) -> str:
    mapping = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "60m",
        "1d": "1d",
        "1w": "1wk",
    }
    if interval not in mapping:
        raise ValueError("Intervalo no soportado por Yahoo Finance")
    return mapping[interval]


def _ensure_utc(ts_like: str | datetime | pd.Timestamp) -> datetime:
    ts = pd.Timestamp(ts_like)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts.to_pydatetime()


def fetch_klines_yahoo(
    symbol: str,
    interval: str,
    start: str | datetime,
    end: str | datetime,
) -> pd.DataFrame:
    if yf is None:
        raise RuntimeError("yfinance no está disponible")
    yint = _yahoo_interval_map(interval)
    start_ts = _ensure_utc(start)
    end_ts = _ensure_utc(end)
    ticker = yf.Ticker(symbol)
    hist = ticker.history(interval=yint, start=start_ts, end=end_ts, auto_adjust=False)
    if hist.empty:
        raise RuntimeError("Yahoo no devolvió datos. Verifica símbolo/intervalo/fechas")
    df = hist.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
    df.index = pd.to_datetime(df.index, utc=True)
    df = df[["open","high","low","close","volume"]]

    # aprox periods/year
    seconds = {
        "1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "1d": 86400, "1w": 604800
    }[interval]
    df.attrs["interval"] = interval
    df.attrs["periods_per_year"] = (365 * 24 * 3600) / seconds
    return df


def fetch_klines(
    symbol: str,
    interval: str,
    start: str | datetime,
    end: str | datetime,
    limit: int = 1000,
    source: str = "binance",
) -> pd.DataFrame:
    if source == "binance":
        return fetch_klines_binance(symbol, interval, start, end, limit)
    elif source == "yahoo":
        return fetch_klines_yahoo(symbol, interval, start, end)
    else:
        raise ValueError("source debe ser 'binance' o 'yahoo'")