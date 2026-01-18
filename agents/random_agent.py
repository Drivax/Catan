import random
from agents.base import Agent

class RandomAgent(Agent):
    def choose_action(self,game,player_id):
        player = game.players[player_id]
        possible=[]

        if player.can_build_city():
            possible.append("city")
        if player.can_build_settlement():
            possible.append("settlement")
        if player.can_build_road():
            possible.append("road")

        if not possible:
            return "pass"

        return random.choice(possible)