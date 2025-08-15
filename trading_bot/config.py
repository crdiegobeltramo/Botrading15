import os
from dataclasses import dataclass


@dataclass
class BinanceConfig:
    api_key: str | None
    api_secret: str | None
    testnet: bool = False


def load_binance_config(testnet: bool = False) -> BinanceConfig:
    return BinanceConfig(
        api_key=os.getenv("BINANCE_API_KEY"),
        api_secret=os.getenv("BINANCE_API_SECRET"),
        testnet=testnet,
    )