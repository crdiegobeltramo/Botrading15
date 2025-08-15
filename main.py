from __future__ import annotations

import argparse
import json

import pandas as pd

from trading_bot.config import load_binance_config
from trading_bot.data import fetch_klines
from trading_bot.strategies import STRATEGY_REGISTRY
from trading_bot.backtester import backtest, summarize_trades
from trading_bot.execution.live_trader import LiveTrader


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Binance Trading Bot with Backtesting")

    sub = parser.add_subparsers(dest="mode", required=True)

    # Backtest
    p_bt = sub.add_parser("backtest", help="Ejecuta un backtest")
    p_bt.add_argument("--symbol", required=True)
    p_bt.add_argument("--interval", required=True, help="Ej: 1m,5m,1h,4h,1d")
    p_bt.add_argument("--start", required=True, help="YYYY-MM-DD")
    p_bt.add_argument("--end", required=True, help="YYYY-MM-DD")
    p_bt.add_argument("--strategy", required=True, choices=list(STRATEGY_REGISTRY.keys()))
    p_bt.add_argument("--initial-capital", type=float, default=1000.0)
    p_bt.add_argument("--fee", type=float, default=0.001)
    p_bt.add_argument("--source", type=str, default="binance", choices=["binance","yahoo"], help="Fuente de datos para backtest")
    # Strategy params (generic)
    p_bt.add_argument("--fast", type=int, default=10)
    p_bt.add_argument("--slow", type=int, default=30)
    p_bt.add_argument("--window", type=int, default=20)
    p_bt.add_argument("--num-std", type=float, default=2.0)

    # Live
    p_live = sub.add_parser("live", help="Ejecuta una orden basada en la última señal (demo)")
    p_live.add_argument("--symbol", required=True)
    p_live.add_argument("--interval", required=True)
    p_live.add_argument("--strategy", required=True, choices=list(STRATEGY_REGISTRY.keys()))
    p_live.add_argument("--testnet", action="store_true")
    p_live.add_argument("--quote-qty", type=float, default=None, help="Cantidad en moneda de cotización para la orden de mercado")
    p_live.add_argument("--source", type=str, default="binance", choices=["binance","yahoo"], help="Fuente de datos para señales")
    p_live.add_argument("--fast", type=int, default=10)
    p_live.add_argument("--slow", type=int, default=30)
    p_live.add_argument("--window", type=int, default=20)
    p_live.add_argument("--num-std", type=float, default=2.0)

    return parser.parse_args()


def build_strategy(name: str, args: argparse.Namespace):
    StrategyCls = STRATEGY_REGISTRY[name]
    params = {
        "fast": args.fast,
        "slow": args.slow,
        "window": args.window,
        "num_std": args.num_std,
    }
    return StrategyCls(params=params)


def run_backtest(args: argparse.Namespace) -> None:
    df = fetch_klines(args.symbol, args.interval, args.start, args.end, source=args.source)
    strat = build_strategy(args.strategy, args)
    position = strat.generate_position(df)

    result = backtest(
        df=df,
        position=position,
        initial_capital=args.initial_capital,
        fee_rate=args.fee,
    )

    trades = summarize_trades(position, result.returns, fee_rate=args.fee)
    output = {
        "metrics": result.metrics | trades,
        "last_equity": float(result.equity.iloc[-1]),
    }
    print(json.dumps(output, indent=2))


def run_live(args: argparse.Namespace) -> None:
    config = load_binance_config(testnet=args.testnet)

    df = fetch_klines(args.symbol, args.interval, pd.Timestamp.utcnow().floor("D") - pd.Timedelta(days=14), pd.Timestamp.utcnow(), source=args.source)
    strat = build_strategy(args.strategy, args)
    position = strat.generate_position(df)

    latest_pos = int(position.iloc[-1])

    trader = LiveTrader(config=config, symbol=args.symbol, testnet=args.testnet)
    order = trader.run_once_from_signal(latest_position=latest_pos, quote_qty=args.quote_qty)

    print(json.dumps({"latest_position": latest_pos, "order": order}, indent=2, default=str))


def main() -> None:
    args = parse_args()
    if args.mode == "backtest":
        run_backtest(args)
    elif args.mode == "live":
        run_live(args)


if __name__ == "__main__":
    main()