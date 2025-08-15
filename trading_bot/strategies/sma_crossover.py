from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .base import Strategy


@dataclass
class SmaCrossover(Strategy):
    def generate_position(self, df: pd.DataFrame) -> pd.Series:
        fast = int(self.params.get("fast", 10))
        slow = int(self.params.get("slow", 30))
        if fast >= slow:
            raise ValueError("'fast' debe ser menor que 'slow'")

        close = df["close"].astype(float)
        sma_fast = close.rolling(fast, min_periods=fast).mean()
        sma_slow = close.rolling(slow, min_periods=slow).mean()
        signal = (sma_fast > sma_slow).astype(int)
        position = signal.ffill().fillna(0)
        position.name = "position"
        return position