from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    equity: pd.Series
    returns: pd.Series
    strategy_returns: pd.Series
    metrics: Dict[str, Any]


def _compute_drawdown(equity: pd.Series) -> pd.Series:
    rolling_max = equity.cummax()
    drawdown = equity / rolling_max - 1.0
    return drawdown


def _calc_metrics(strategy_returns: pd.Series, equity: pd.Series, periods_per_year: float) -> Dict[str, Any]:
    total_return = equity.iloc[-1] / equity.iloc[0] - 1.0
    avg = strategy_returns.mean()
    vol = strategy_returns.std(ddof=0)
    sharpe = (avg * periods_per_year) / vol if vol > 0 else np.nan
    years = len(strategy_returns) / periods_per_year if periods_per_year > 0 else np.nan
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1 if years and years > 0 else np.nan
    dd = _compute_drawdown(equity)
    max_dd = dd.min()
    return {
        "total_return": float(total_return),
        "cagr": float(cagr) if cagr == cagr else np.nan,  # handle nan
        "sharpe": float(sharpe) if sharpe == sharpe else np.nan,
        "max_drawdown": float(max_dd),
    }


def _infer_periods_per_year_from_df(df: pd.DataFrame) -> float:
    if len(df.index) < 2:
        return 365.0
    deltas = df.index.to_series().diff().dropna().dt.total_seconds()
    if deltas.empty:
        return 365.0
    median_seconds = float(deltas.median())
    return (365 * 24 * 3600) / median_seconds


def backtest(
    df: pd.DataFrame,
    position: pd.Series,
    initial_capital: float = 1000.0,
    fee_rate: float = 0.001,
    periods_per_year: float | None = None,
) -> BacktestResult:
    df = df.copy()
    position = position.reindex(df.index).fillna(0).astype(float)

    close = df["close"].astype(float)
    asset_returns = close.pct_change().fillna(0.0)

    pos_shifted = position.shift(1).fillna(0.0)
    gross_strategy_returns = asset_returns * pos_shifted

    trade_change = position.diff().abs().fillna(0.0)
    trade_costs = trade_change * fee_rate

    strategy_returns = gross_strategy_returns - trade_costs

    equity = (1.0 + strategy_returns).cumprod() * initial_capital

    if periods_per_year is None:
        periods_per_year = df.attrs.get("periods_per_year") or _infer_periods_per_year_from_df(df)

    metrics = _calc_metrics(strategy_returns, equity, periods_per_year)

    result = BacktestResult(
        equity=equity,
        returns=asset_returns,
        strategy_returns=strategy_returns,
        metrics=metrics,
    )

    return result


def summarize_trades(position: pd.Series, asset_returns: pd.Series, fee_rate: float = 0.001) -> Dict[str, Any]:
    pos = position.fillna(0).astype(int)
    entries = (pos.diff() == 1)
    exits = (pos.diff() == -1)

    entry_indices = list(pos.index[entries])
    exit_indices = list(pos.index[exits])

    if len(exit_indices) < len(entry_indices):
        exit_indices.append(pos.index[-1])

    trade_returns = []
    for e, x in zip(entry_indices, exit_indices):
        period_rets = asset_returns.loc[e:x]
        gross = float((1 + period_rets).prod() - 1)
        # two sides cost expected (enter + exit) if full close
        net = gross - 2 * fee_rate
        trade_returns.append(net)

    trade_returns = np.array(trade_returns)
    num_trades = int(len(trade_returns))
    wins = int((trade_returns > 0).sum())
    win_rate = float(wins / num_trades) if num_trades > 0 else float("nan")

    return {
        "num_trades": num_trades,
        "win_rate": win_rate,
        "avg_trade_return": float(trade_returns.mean()) if num_trades > 0 else float("nan"),
    }