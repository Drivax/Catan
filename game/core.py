import random

from collections import defaultdict, Counter

from game.board import Board

from game.player import Player

from agents.base import Agent

from agents.random_agent import RandomAgent

from game.rules import RESOURCES, VICTORY_POINTS_TO_WIN

 

class CatanGame:

    def __init__(self, agents: list[Agent], num_players=4):

        if len(agents) != num_players:

            raise ValueError("One agent per player needed")

        self.num_players = num_players

        self.agents = agents

        self.players = [Player(i) for i in range(num_players)]

        self.board = Board()

        self.longest_road_leader = None

        self.longest_road_length = 0

        self.setup()

        self.current_player = 0

        self.turn_number = 0

        self.winner = None

 

    # -------------------------------------------------------------------------

    # Setup initial

    # -------------------------------------------------------------------------

 

    def setup(self):
        """
        Catan setup with randomized snake-draft order:
        - A random permutation of players is chosen at the start of each game.
        - Round 1 (forward): each player places 1 settlement + 1 road and collects
          resources from the adjacent hex tiles.
        - Round 2 (reverse): players go in the opposite order, each placing their
          2nd settlement + 1 road and collecting resources.
        The last player in Round 1 therefore places twice in a row (standard Catan
        snake draft).  Settlement placement is delegated to each agent.
        """
        all_vertices = list(self.board.get_all_vertices())
        placed_vertices = set()

        # Randomize player order for this game (changes every game)
        player_order = list(range(self.num_players))
        random.shuffle(player_order)
        print(f"Setup order: {player_order}")

        def get_valid_vertices():
            """Vertices that are unoccupied and not adjacent to any placed settlement."""
            result = []
            for v in all_vertices:
                if v in placed_vertices:
                    continue
                neighbors = set(self.board.vertex_neighbors.get(v, []))
                if not any(pv in neighbors for pv in placed_vertices):
                    result.append(v)
            return result

        def place_one_settlement(pid, settlement_num):
            player = self.players[pid]
            valid_vertices = get_valid_vertices()

            if not valid_vertices:
                return

            chosen_v = None
            try:
                chosen_v = self.agents[pid].choose_initial_settlement(self, pid, valid_vertices)
            except Exception as exc:
                print(f"  WARNING: agent {pid} raised an error in choose_initial_settlement: {exc}. Falling back to random.")

            # Fallback to random if the agent returned an invalid vertex
            if chosen_v is None or chosen_v not in valid_vertices:
                chosen_v = random.choice(valid_vertices)

            if self.board.place_settlement(pid, chosen_v):
                player.build_settlement(free_cost=True)
                placed_vertices.add(chosen_v)
                all_vertices.remove(chosen_v)
                print(f"J{pid} settlement {settlement_num}/2 on {chosen_v}")

                produced = self.board.produce_from_vertex(chosen_v)
                if produced:
                    player.add_resources(produced)

            # Place 1 road (random direction from the new settlement)
            possible_roads = self.board.get_possible_roads(pid)
            if possible_roads:
                edge = random.choice(possible_roads)
                self.board.place_road(pid, edge)
                player.build_road(free_cost=True)

        # ROUND 1: forward order
        for pid in player_order:
            place_one_settlement(pid, 1)

        # ROUND 2: reverse order (snake draft – last player goes first)
        for pid in reversed(player_order):
            place_one_settlement(pid, 2)

 

    # -------------------------------------------------------------------------

    # Mecanique de jeu

    # -------------------------------------------------------------------------

 

    def roll_dice(self):

        return random.randint(1, 6) + random.randint(1, 6)

 

    def play_one_turn(self):

        self.turn_number += 1

        player = self.players[self.current_player]

        self.robber_turn = False

 

        dice = self.roll_dice()

        print(f"[{self.turn_number:3d}] Player {self.current_player} rolls a {dice}")

 

        # --- Phase voleur (7) ---

        if dice == 7:

            for p in self.players:

                discarded = p.discard_half()

                if discarded:

                    print(f"  J{p.pid} loses {dict(discarded)}")

            self.robber_turn = True

 

            # FIX: l'agent choisit OU deplacer le voleur

            action = self.agents[self.current_player].choose_action(self, self.current_player)

            if action.action == 'move_robber' and action.target is not None:

                new_pos = action.target

                old_pos = self.board.robber_pos

                self.board.move_robber(new_pos)

                print(f"  -> Voleur deplace de {old_pos} -> {new_pos}")

            else:

                # L'agent ne choisit pas -> deplacement aleatoire

                new_robber_pos = random.choice(list(self.board.hexes.keys()))

                self.board.move_robber(new_robber_pos)

                print(f"  -> Voleur deplace aleatoirement sur {new_robber_pos}")

 

            # Vol de ressource

            candidates = self.board.get_steal_candidates(self.board.robber_pos, self.current_player)

            valid_victims = [

                pid for pid in candidates

                if sum(self.players[pid].resources.values()) >= 1

            ]

 

            if valid_victims:

                # Voler le joueur le plus riche parmi les candidats valides

                victim_pid = max(valid_victims, key=lambda pid: sum(self.players[pid].resources.values()))

                victim = self.players[victim_pid]

                stolen_res = random.choice(list(victim.resources.elements()))

                victim.resources[stolen_res] -= 1

                player.resources[stolen_res] += 1

                print(f"  -> J{self.current_player} vole {stolen_res} a J{victim_pid}")

            else:

                print("  -> Rien a voler")

 

        # --- Phase production (non-7) ---

        else:

            produced = self.board.produce(dice)

            for pid, res in produced.items():

                if sum(res.values()) > 0:

                    self.players[pid].add_resources(res)

                    print(f"  -> J{pid} recoit {dict(res)}")

 

        # Affichage ressources

        for p in self.players:

            res_str = " | ".join(

                f"{r.capitalize():5}: {v:2d}"

                for r, v in p.resources.items() if v > 0

            )

            print(f"  J{p.pid} {p.victory_points:2d} pts -> {res_str}")

 

        # --- Phase echange joueurs ---

        self.handle_player_trade(self.current_player)

 

        # --- Phase echange banque ---

        agent = self.agents[self.current_player]

        player = self.players[self.current_player]

        port_types = self.board.get_player_ports(player.pid)

        print(f"  Trade phase - ports accessibles : {port_types or 'None'}")

 

        # FIX: choose_trade retourne un dict avec les bonnes cles

        trade_decision = agent.choose_trade(self, self.current_player)

        if trade_decision:

            give = trade_decision['give']

            receive = trade_decision['receive']

            ratio = trade_decision['ratio']

            if player.execute_bank_trade(give, receive, ratio):

                print(f"  -> Trade banque {ratio}:1 | donne {ratio}x{give} -> recoit 1x{receive}")

            else:

                print(f"  -> Trade impossible ({ratio}:1 {give} -> {receive})")

 

        # --- Phase construction ---

        self.robber_turn = False  # Reinitialiser pour la phase construction

        action = self.agents[self.current_player].choose_action(self, self.current_player)

        player = self.players[self.current_player]

        acted = False

 

        if action.action == 'build_settlement':

            v = action.target

            if player.can_build_settlement() and self.board.place_settlement(player.pid, v):

                player.build_settlement()

                print(f"  -> Colonie sur {v} ({player.victory_points} pts)")

                acted = True

 

        elif action.action == 'build_city':

            v = action.target

            if player.can_build_city() and self.board.upgrade_to_city(player.pid, v):

                player.build_city()

                print(f"  -> Ville sur {v} ({player.victory_points} pts)")

                acted = True

 

        elif action.action == 'build_road':

            edge = action.target

            if player.can_build_road() and self.board.place_road(player.pid, edge):

                player.build_road()

                print(f"  -> Route sur {list(edge)}")

                acted = True

            self.update_longest_road()

 

        else:

            print("  -> pass")

 

        # Verification victoire

        if player.victory_points >= VICTORY_POINTS_TO_WIN:

            self.winner = player.pid

            print(f"\nVICTOIRE joueur {player.pid} ({player.victory_points} points)")

 

        self.current_player = (self.current_player + 1) % self.num_players

 

    # -------------------------------------------------------------------------

    # Longest road

    # -------------------------------------------------------------------------

 

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

                # Retirer les points a l'ancien leader

                if self.longest_road_leader is not None:

                    old = self.players[self.longest_road_leader]

                    old.victory_points -= 2

                    print(f"  Longest road perdu par J{self.longest_road_leader} (-2 pts)")

                # Donner les points au nouveau leader

                new = self.players[leader]

                new.victory_points += 2

                print(f"  *** LONGEST ROAD *** J{leader} gagne +2 pts (longueur {max_len})")

                self.longest_road_leader = leader

                self.longest_road_length = max_len

        else:

            # FIX: si personne n'a 5 routes, retirer les points si quelqu'un les avait

            if self.longest_road_leader is not None:

                old = self.players[self.longest_road_leader]

                old.victory_points -= 2

                print(f"  Longest road perdu par J{self.longest_road_leader} (plus de 5 routes)")

                self.longest_road_leader = None

                self.longest_road_length = 0

 

    # -------------------------------------------------------------------------

    # Boucle principale

    # -------------------------------------------------------------------------

 

    def run_until_end(self, max_turns=500):

        while self.winner is None and self.turn_number < max_turns:

            self.play_one_turn()

        if self.winner is None:

            print("Limite de tours atteinte, match nul force")

        return self.winner

 

    # -------------------------------------------------------------------------

    # Echange entre joueurs

    # -------------------------------------------------------------------------

 

    def handle_player_trade(self, pid):

        player = self.players[pid]

        print(f"  [Echange joueurs] J{pid} peut proposer un trade")

 

        # Agent chooses trade (or defaults to random) 

        trade_offer = self.agents[pid].choose_player_trade(self, pid)

        if trade_offer is None:

            return

 

        # Trade negotiation

        target_pid = trade_offer.target.get('target_pid')

        give_res = trade_offer.target.get('give_res')

        give_amount = trade_offer.target.get('give_amount')

        receive_res = trade_offer.target.get('receive_res')

        receive_amount = trade_offer.target.get('receive_amount')

 

        print(f"  -> J{pid} propose a J{target_pid} : {give_amount}x{give_res} contre {receive_amount}x{receive_res}")

 

        target = self.players[target_pid]

        accept = False

 

        # Target's acceptance logic: check if beneficial

        if target.resources[receive_res] < receive_amount:

            accept = False

        else:

            # With scarce resources, be more willing to trade

            target_needs_give = (target.resources[give_res] <= 1)

            target_needs_receive = (target.resources[receive_res] <= 2)  # More lenient threshold

            target_has_enough_give = (target.resources[give_res] >= 2)

            

            if target_has_enough_give and target_needs_receive:

                # Target has abundance and wants what we offer - YES

                accept = True

            elif target_needs_give and not target_needs_receive:

                # Target needs what we're giving but doesn't need what we want - NO

                accept = False

            elif target_needs_give and target_needs_receive:

                # Both benefit - high probability YES (resources are scarce)

                accept = random.random() < 0.85

            elif target_has_enough_give:

                # Target has extras - allow trade

                accept = random.random() < 0.6

            else:

                # Neutral - slight rejection

                accept = random.random() < 0.3

 

        if accept:

            print(f"  -> J{target_pid} accepte")

            player.execute_trade(give_res, give_amount, receive_res, receive_amount)

            target.execute_trade(receive_res, receive_amount, give_res, give_amount)

            print(f"  -> J{pid} donne {give_amount} {give_res} -> recoit {receive_amount} {receive_res}")

            print(f"  -> J{target_pid} donne {receive_amount} {receive_res} -> recoit {give_amount} {give_res}")

        else:

            print(f"  -> J{target_pid} refuse")