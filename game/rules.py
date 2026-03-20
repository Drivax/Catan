from collections import Counter
from dataclasses import dataclass

COST_ROAD       = Counter(wood=1, brick=1)
COST_SETTLEMENT = Counter(wood=1, brick=1, sheep=1, wheat=1)
COST_CITY       = Counter(wheat=2, ore=3)

POINTS_DIC={"road":0,"colony":1,"city":2}

RESOURCES = ["wood", "brick", "sheep", "wheat", "ore"]

VICTORY_POINTS_TO_WIN = 10


