# Turn gestion, victory conditions

import random
from collections import defaultdict
from game.board import Board
from game.player import Player
from agents.base import Agent
from agents.random_agent import RandomAgent

class CatanGame:
    def __init__(self,agents:list[Agent], num_players=4):
        if len(agents) != num_players:
            raise ValueError("One agent per player needed")
        self.num_players = num_players
        self.agents=agents
        self.players = [Player(i) for i in range(num_players)]
        self.board = Board()
        self.current_player = 0
        self.turn_number = 0
        self.winner = None

    def roll_dice(self):
        return random.randint(1,6) + random.randint(1,6)

    def play_one_turn(self):
        self.turn_number += 1
        player = self.players[self.current_player]

        dice = self.roll_dice()
        print(f"[{self.turn_number:3d}] Player {self.current_player} rolls a  {dice}")

        if dice == 7:
            # TEMPORARY simplified robber 
            self.board.robber_hex = random.randrange(len(self.board.tiles))
            # Discard card if >=7
        else:
            produced = self.board.produce(dice)
            for pid, res in produced.items():
                self.players[pid].add_resources(res)
                if pid == self.current_player and sum(res.values()) > 0:
                                    print(f"   → produced : {dict(res)}")
        # trade phase

        # construction phase
        action = self.agents[self.current_player].choose_action(self, self.current_player)
        
        if action == "city" and player.build_city():
            print(f"  → built a city !")
        elif action == "settlement" and player.build_settlement():
            print(f"  → built a colony !")
        elif action == "road" and player.build_road():
            print(f"  → built a road")
        else:
                    print(f"   → pass")

        if player.victory_points >= 10:
            self.winner = player.pid
            print(f"\nVICTOIRE  player {player.pid} ({player.victory_points} points)")

        self.current_player = (self.current_player + 1) % self.num_players

    def run_until_end(self,max_turns=500):
        while self.winner is None and self.turn_number < max_turns:
            self.play_one_turn()
        if self.winner is None:
              print("Turns limit reached, forced draw")
        return self.winner