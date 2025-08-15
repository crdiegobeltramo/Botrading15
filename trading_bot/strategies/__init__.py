from .sma_crossover import SmaCrossover
from .bbands import BollingerBands


STRATEGY_REGISTRY = {
    "sma_crossover": SmaCrossover,
    "bbands": BollingerBands,
}