from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .base import Strategy


@dataclass
class BollingerBands(Strategy):
    def generate_position(self, df: pd.DataFrame) -> pd.Series:
        window = int(self.params.get("window", 20))
        num_std = float(self.params.get("num_std", 2.0))

        close = df["close"].astype(float)
        ma = close.rolling(window, min_periods=window).mean()
        std = close.rolling(window, min_periods=window).std()
        upper = ma + num_std * std
        lower = ma - num_std * std

        entries = (close < lower).astype(int)
        exits = (close > ma).astype(int)

        position = pd.Series(0, index=df.index, dtype=int)
        in_pos = False
        for idx in df.index:
            if not in_pos and entries.loc[idx] == 1:
                in_pos = True
            elif in_pos and exits.loc[idx] == 1:
                in_pos = False
            position.loc[idx] = 1 if in_pos else 0

        position.name = "position"
        return position