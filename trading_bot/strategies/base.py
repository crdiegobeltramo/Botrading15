from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pandas as pd


@dataclass
class Strategy:
    params: Dict

    def generate_position(self, df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError