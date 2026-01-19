from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass

class Agent(ABC):
    @abstractmethod
    def choose_action(self, game, player_id):
        pass

@dataclass
class Action:
    action: str  
    target: Any = None  