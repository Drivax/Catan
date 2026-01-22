# Turn gestion, victory conditions

import random
from collections import defaultdict
from game.board import Board
from game.player import Player
from agents.base import Agent
from agents.random_agent import RandomAgent
from game.rules import RESOURCES

class CatanGame:
    def __init__(self,agents:list[Agent], num_players=4):
        if len(agents) != num_players:
            raise ValueError("One agent per player needed")
        self.num_players = num_players
        self.agents=agents
        self.players = [Player(i) for i in range(num_players)]
        self.board = Board()
        self.longest_road_leader = None
        self.longest_road_length = 0
        self.setup()
        self.current_player = 0
        self.turn_number = 0
        self.winner = None

    def setup(self):
        all_vertices = list(self.board.get_all_vertices())
        random.shuffle(all_vertices)
        placed_vertices=set()
        vertex_index = 0
        for pid in range(self.num_players):
            player = self.players[pid]
            count=0
            while count<2:  
                if not all_vertices:
                    break
                v = all_vertices.pop(0)
                valid = True
                for existing_v in placed_vertices:
                    if self.board.approx_distance(v, existing_v) < 2:
                        valid = False
                        break
                if valid:
                    if self.board.place_settlement(pid, v):
                        player.build_settlement(free_cost=True)
                        placed_vertices.add(v)
                        print(f"J{pid} settlement {count+1}/2 on {v}")
                        if count == 0:  
                            produced = self.board.produce_from_vertex(v)
                            if produced:
                                player.add_resources(produced)
                        count += 1

                    else:
                        all_vertices.append(v)

            # 2 roads
            possible_roads = self.board.get_possible_roads(pid)
            for _ in range(2):
                if possible_roads:
                    edge = random.choice(possible_roads)
                    self.board.place_road(pid, edge)
                    player.build_road(free_cost=True)
                    print(f"J{pid} road on {list(edge)}")
                    possible_roads = self.board.get_possible_roads(pid)
                    
    def roll_dice(self):
        return random.randint(1,6) + random.randint(1,6)

    def play_one_turn(self):
        self.turn_number += 1
        player = self.players[self.current_player]
        self.robber_turn = False

        dice = self.roll_dice()
        print(f"[{self.turn_number:3d}] Player {self.current_player} rolls a  {dice}")

        if dice == 7:
            for p in self.players:
                discarded = p.discard_half()
                if discarded:
                    print(f"     J{p.pid} loses {dict(discarded)} ")
                    
            self.robber_turn = True
            action = self.agents[self.current_player].choose_action(self, self.current_player)
            if action.action == 'move_robber':
                new_pos = action.target
                old_pos = self.board.robber_pos
                self.board.move_robber(new_pos)
                print(f"   → Voleur moving from  {old_pos} → {new_pos}")
            else:
                print("   → Voleur stays on position")

            new_robber_pos = random.choice(list(self.board.hexes.keys()))
            self.board.move_robber(new_robber_pos)
            print("   → robber going on random pos")
           
            candidates = self.board.get_steal_candidates(self.board.robber_pos, self.current_player)
            valid_victims = []
            for pid in candidates:
                victim = self.players[pid]
                if sum(victim.resources.values()) >= 1:
                    valid_victims.append(pid)
            scored_victims = [
                (pid, sum(self.players[pid].resources.values()))
                for pid in candidates
            ]
            if valid_victims:
                victim_pid = random.choice(valid_victims)
                victim_pid = max(scored_victims, key=lambda x: x[1])[0] 
                
                victim = self.players[victim_pid]
                if victim.resources:
                    stolen_res = random.choice(list(victim.resources.elements()))  
                    victim.resources[stolen_res] -= 1
                    player.resources[stolen_res] += 1
                    print(f"   →  J{self.current_player} steals {stolen_res} to J{victim_pid}")
                else:
                    print(f"   → J{victim_pid} doesnt steal anything")
            else:
                print("   → nothing to steal")
           
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
        self.handle_player_trade(self.current_player)

        agent=self.agents[self.current_player]
        player = self.players[self.current_player]
        port_types=self.board.get_player_ports(player.pid)
        print(f"   Trade phasee - accessibles ports  : {port_types or 'None'}")

        trade_decision = agent.choose_trade(self, self.current_player)
        if trade_decision:
            give = trade_decision['give']
            receive = trade_decision['receive']
            ratio = trade_decision['ratio']
            
            if player.execute_bank_trade(give, receive, ratio):
                print(f"   → trade bank {ratio}:1 | gives {ratio}×{give} → gets 1×{receive}")
            else:
                print(f"   →  impossible ({ratio}:1 {give} → {receive})")


        # construction phase
        action = self.agents[self.current_player].choose_action(self, self.current_player)
        player = self.players[self.current_player]
        acted = False

        if action.action == 'build_settlement':
            v = action.target
            if player.can_build_settlement() and self.board.place_settlement(player.pid, v):
                player.build_settlement()
                print(f"   → colony sur {v} ({player.victory_points} pts)")
                acted = True
        elif action.action == 'build_city':
            v = action.target
            if player.can_build_city() and self.board.upgrade_to_city(player.pid, v):
                player.build_city()
                print(f"   → city sur {v} ({player.victory_points} pts)")
                acted = True
        elif action.action == 'build_road':
            edge = action.target
            if player.can_build_road() and self.board.place_road(player.pid, edge):
                player.build_road()
                print(f"   → road on{list(edge)}")
                acted = True
                self.update_longest_road()  
        else:
            print("   → pass")
        if player.victory_points >= 10:
            self.winner = player.pid
            print(f"\nVICTOIRE  player {player.pid} ({player.victory_points} points)")

        self.current_player = (self.current_player + 1) % self.num_players

    def update_longest_road(self):
        max_len = 0
        leader = None
        for pid in range(self.num_players):
            length = self.board.get_longest_road_length(pid)
            if length > max_len:
                max_len = length
                leader = pid
        if max_len >= 5:
            if self.longest_road_leader != leader:
                if self.longest_road_leader is not None:
                    old = self.players[self.longest_road_leader]
                    old.victory_points -= 2
                    print(f"   Longest road perdu par J{self.longest_road_leader} (-2 pts)")
                new = self.players[leader]
                new.victory_points += 2
                print(f"   *** LONGEST ROAD *** J{leader} gagne +2 pts (longueur {max_len})")
                self.longest_road_leader = leader
                self.longest_road_length = max_len

    def run_until_end(self,max_turns=500):
        while self.winner is None and self.turn_number < max_turns:
            self.play_one_turn()
        if self.winner is None:
              print("Turns limit reached, forced draw")
        return self.winner
    
    def handle_player_trade(self, pid):
        player = self.players[pid]
        agent = self.agents[pid]

        print(f"   [Échange joueurs] J{pid} peut proposer un trade")

        # L'agent décide s'il veut proposer (random pour RandomAgent)
        if random.random() < 0.4:  # 40% de chance de proposer un trade
            print("   → J{pid} décide de ne pas proposer de trade")
            return

        # Choix de l'adversaire (random parmi les autres)
        other_pids = [i for i in range(self.num_players) if i != pid]
        if not other_pids:
            return
        target_pid = random.choice(other_pids)
        target = self.players[target_pid]

        # Ressources que le joueur a en quantité suffisante
        my_abundant = [r for r in RESOURCES if player.resources[r] >= 1]

        if not my_abundant:
            print("   → J{pid} n'a rien à donner")
            return

        give_res = random.choice(my_abundant)
        give_amount = 1 if random.random() < 0.7 else 2  # 1:1 ou 2:1

        # Ce qu'il veut recevoir (quelque chose qu'il a peu)
        candidates_receive = [r for r in RESOURCES if player.resources[r] <= 1 and r != give_res]
        if not candidates_receive:
            candidates_receive = [r for r in RESOURCES if r != give_res]
        receive_res = random.choice(candidates_receive)
        receive_amount = 1  # pour l'instant on demande toujours 1

        print(f"   → J{pid} propose à J{target_pid} : {give_amount}×{give_res} contre 1×{receive_res}")

        # L'adversaire décide s'il accepte (logique très basique)
        accept = False

        # Accepte si :
        # - il a assez de la ressource demandée
        # - et qu'il a peu de la ressource qu'il reçoit (ou aléatoire)
        if target.resources[receive_res] >= receive_amount:
            if target.resources[give_res] <= 2 or random.random() < 0.6:
                accept = True

        if accept:
            print(f"   → J{target_pid} **accepte**")
            # Exécution de l'échange
            player.execute_trade(give_res, give_amount, receive_res, receive_amount)
            target.execute_trade(receive_res, receive_amount, give_res, give_amount)
            print(f"   → Échange effectué : J{pid} donne {give_amount} {give_res} → reçoit 1 {receive_res}")
            print(f"   → J{target_pid} donne 1 {receive_res} → reçoit {give_amount} {give_res}")
        else:
            print(f"   → J{target_pid} **refuse**")