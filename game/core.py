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
        self.setup()
        self.current_player = 0
        self.turn_number = 0
        self.winner = None

    def setup(self):
        all_vertices = self.board.get_all_vertices()
        random.shuffle(all_vertices)
        
        vertex_index = 0
        for pid in range(self.num_players):
            for _ in range(2):  
                while vertex_index < len(all_vertices):
                    vkey = all_vertices[vertex_index]
                    vertex_index += 1
                    if vkey not in self.board.buildings:
                        self.board.place_settlement(pid, vkey)
                        self.players[pid].build_settlement()
                        break

    def roll_dice(self):
        return random.randint(1,6) + random.randint(1,6)

    def play_one_turn(self):
        self.turn_number += 1
        player = self.players[self.current_player]

        dice = self.roll_dice()
        print(f"[{self.turn_number:3d}] Player {self.current_player} rolls a  {dice}")

        if dice == 7:
            new_robber_pos = random.choice(list(self.board.hexes.keys()))
            self.board.move_robber(new_robber_pos)
            print("   → robber going on random pos")
            # Discard card if >=7
        else:
            produced = self.board.produce(dice)
            for pid, res in produced.items():
                if sum(res.values()) > 0:
                    self.players[pid].add_resources(res)
                    print(f"   → J{pid} gets {dict(res)}")

        for p in self.players:
            res_str = " | ".join(f"{r.capitalize():5}: {v:2d}" for r,v in p.resources.items() if v > 0)
            pts = p.victory_points
            print(f"    J{p.pid}  {pts:2d} pts  →  {res_str}")

        # trade phase

        # construction phase
        action = self.agents[self.current_player].choose_action(self, self.current_player)
        player = self.players[self.current_player]
        acted = False
        
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