from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import math
from binance.spot import Spot as SpotClient

from trading_bot.config import BinanceConfig


@dataclass
class LiveTrader:
    config: BinanceConfig
    symbol: str
    testnet: bool = False

    def _client(self) -> SpotClient:
        if self.testnet:
            return SpotClient(api_key=self.config.api_key, api_secret=self.config.api_secret, base_url="https://testnet.binance.vision")
        return SpotClient(api_key=self.config.api_key, api_secret=self.config.api_secret)

    def _get_symbol_filters(self) -> dict:
        client = self._client()
        info = client.exchange_info(symbol=self.symbol)
        return info["symbols"][0]["filters"]

    def _get_base_quote(self) -> Tuple[str, str]:
        client = self._client()
        info = client.exchange_info(symbol=self.symbol)
        s = info["symbols"][0]
        return s["baseAsset"], s["quoteAsset"]

    def _get_step_size(self) -> float:
        filters = self._get_symbol_filters()
        for f in filters:
            if f.get("filterType") == "LOT_SIZE":
                return float(f["stepSize"])
        return 0.000001

    def _round_step(self, qty: float, step: float) -> float:
        if step <= 0:
            return qty
        return math.floor(qty / step) * step if step < 1 else float(int(qty))

    def _get_last_price(self) -> float:
        client = self._client()
        t = client.ticker_price(symbol=self.symbol)
        return float(t["price"])  # type: ignore

    def _get_free_base_balance(self) -> float:
        client = self._client()
        base, _ = self._get_base_quote()
        acc = client.account()
        for b in acc.get("balances", []):
            if b.get("asset") == base:
                return float(b.get("free", 0))
        return 0.0

    def place_market_order_quote(self, quote_qty: float, side: str = "BUY") -> dict:
        client = self._client()
        return client.new_order(
            symbol=self.symbol,
            side=side,
            type="MARKET",
            quoteOrderQty=str(quote_qty),
        )

    def place_market_order_qty(self, quantity: float, side: str = "SELL") -> dict:
        client = self._client()
        step = self._get_step_size()
        qty = self._round_step(quantity, step)
        return client.new_order(
            symbol=self.symbol,
            side=side,
            type="MARKET",
            quantity=str(qty),
        )

    def run_once_from_signal(self, latest_position: int, quote_qty: Optional[float] = None) -> Optional[dict]:
        if quote_qty is None:
            return None
        if latest_position == 1:
            return self.place_market_order_quote(quote_qty=quote_qty, side="BUY")
        elif latest_position == 0:
            try:
                price = self._get_last_price()
            except Exception:
                price = None
            if price and price > 0:
                qty = quote_qty / price
            else:
                qty = self._get_free_base_balance()
            return self.place_market_order_qty(quantity=qty, side="SELL")
        else:
            return None