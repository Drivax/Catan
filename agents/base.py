from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass

class Agent(ABC):
    @abstractmethod
    def choose_action(self, game, player_id):
        pass

    @abstractmethod
    def choose_initial_settlement(self, game, player_id, valid_vertices):
        """Choose a vertex for initial settlement placement from valid_vertices."""
        pass

@dataclass
class Action:
    action: str  
    target: Any = None  