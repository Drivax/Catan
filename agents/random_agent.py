import random

from agents.base import Agent, Action

from game.rules import RESOURCES

class RandomAgent(Agent):

    def __init__(self, trade_chaos=0.0, sheep_hoarder=False, dumb_thief=False):
        """
        Args:
            trade_chaos (float): Probability of offering/accepting bad trades [0.0-1.0]
            sheep_hoarder (bool or float): If True/1.0, refuses to give sheep away
            dumb_thief (bool): If True, always steals from leader instead of weakest player
        """
        super().__init__()
        self.trade_chaos = max(0.0, min(1.0, trade_chaos))  # Clamp [0, 1]
        self.sheep_hoarder = 1 if sheep_hoarder else 0
        self.dumb_thief = 1 if dumb_thief else 0

    def choose_starting_settlement(self, game, pid, valid_vertices):
        """
        Choose starting settlement randomly from valid options.
        """
        if not valid_vertices:
            return None
        return random.choice(valid_vertices)

 

    def choose_action(self, game, player_id):

        player = game.players[player_id]

        board = game.board

 

        # 1. Tour du voleur -> on le deplace

        if hasattr(game, 'robber_turn') and game.robber_turn:

            if self.dumb_thief:
                # Dumb thief: always target the leader
                leader_pid = max(range(game.num_players), key=lambda i: game.players[i].victory_points)
                best_hex = None
                for hex_pos in board.get_all_hexes():
                    adj = board.get_adjacent_players(hex_pos)
                    if any(p == leader_pid for p, _ in adj):
                        best_hex = hex_pos
                        break
                if not best_hex:
                    best_hex = random.choice(board.get_all_hexes())
            else:
                # Normal: target hex with most opponents
                best_hex = None
                max_opponents = -1
                for hex_pos in board.get_all_hexes():
                    adj = board.get_adjacent_players(hex_pos)
                    opponents = len([p for p, _ in adj if p != player_id])
                    if opponents > max_opponents:
                        max_opponents = opponents
                        best_hex = hex_pos

            target = best_hex if best_hex else random.choice(board.get_all_hexes())

            return Action('move_robber', target)

 

        # 2. Priorite : construire une ville si possible

        own_settlements = [

            v for v, (p, t) in board.buildings.items()

            if p == player_id and t == 'settlement'

        ]

        if player.can_build_city() and own_settlements:

            return Action('build_city', random.choice(own_settlements))

 

        # 3. Construire une colonie sur un vertex valide (respecte la distance)

        if player.can_build_settlement():

            # FIX: filtrer les vertices qui respectent la regle de distance

            valid_vertices = []

            for v in board.get_all_vertices():

                if v in board.buildings:

                    continue

                too_close = any(

                    board.approx_distance(v, existing_v) < 2

                    for existing_v in board.buildings

                )

                if not too_close:

                    valid_vertices.append(v)

            if valid_vertices:

                return Action('build_settlement', random.choice(valid_vertices))

 

        # 4. Construire une route

        possible_roads = board.get_possible_roads(player_id)

        if player.can_build_road() and possible_roads:

            return Action('build_road', random.choice(possible_roads))

 

        # 5. Passer

        return Action('pass')

 

    def choose_trade(self, game, pid):

        """

        Decide si on fait un trade banque (4:1 / 3:1 / 2:1).

        Respects trade_chaos and sheep_hoarder parameters.

        """

        player = game.players[pid]

        ports = game.board.get_player_ports(pid)

 

        total = sum(player.resources.values())

        if total < 2:

            return None

 

        # Ressource la plus abondante

        if not player.resources:

            return None

        abundant = max(player.resources, key=player.resources.get)

        # Sheep hoarder refuses to give sheep

        if self.sheep_hoarder and abundant == 'sheep':

            return None


        if player.resources[abundant] < 2:

            return None

 

        # Ce qu'on veut recevoir (priorite : ce qu'on a peu)

        candidates = [r for r in RESOURCES if r != abundant and player.resources[r] <= 2]

        if not candidates:

            candidates = [r for r in RESOURCES if r != abundant]

        if not candidates:

            return None

        want = random.choice(candidates)

 

        ratio = player.can_trade_to_bank(abundant, want, ports)

        if ratio:

            # trade_chaos: sometimes make bad trades (give more than good ratio)

            if random.random() < self.trade_chaos:

                ratio = min(4, ratio + random.randint(1, 2))  # Worse ratio (give more)


            # FIX: retourner un dict avec les cles attendues par core.py

            return {

                'give': abundant,

                'receive': want,

                'ratio': ratio,

            }

        return None

 

    def choose_player_trade(self, game, pid):

        """

        Propose un echange avec un autre joueur.

        Respects trade_chaos and sheep_hoarder parameters.

        """

        player = game.players[pid]

        others = [p for i, p in enumerate(game.players) if i != pid]

 

        if sum(player.resources.values()) < 2:

            return None

 

        give_res = max(player.resources, key=player.resources.get)

        # Sheep hoarder refuses to give sheep

        if self.sheep_hoarder and give_res == 'sheep':

            # Choose a different resource if possible

            alternatives = [r for r in RESOURCES if player.resources.get(r, 0) > 0 and r != 'sheep']

            if alternatives:

                give_res = max(alternatives, key=lambda r: player.resources.get(r, 0))

            else:

                return None


        if player.resources[give_res] < 1:

            return None

 

        target_player = random.choice(others)

 

        candidates = [r for r in RESOURCES if player.resources[r] <= 1 and r != give_res]

        if not candidates:

            candidates = [r for r in RESOURCES if r != give_res]

        receive_res = random.choice(candidates)

 

        give_amount = 1 if player.resources[give_res] <= 3 else 2


        # trade_chaos: sometimes make bad trades (give more than receiving)

        if random.random() < self.trade_chaos:

            give_amount = min(3, give_amount + 1)  # Give more

 

        return Action(

            action='trade_player',

            target={

                'target_pid': target_player.pid,

                'give_res': give_res,

                'give_amount': give_amount,

                'receive_res': receive_res,

                'receive_amount': 1

            }

        )