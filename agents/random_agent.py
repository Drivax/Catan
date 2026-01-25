import random
from agents.base import Agent, Action
from game.rules import RESOURCES


class RandomAgent(Agent):
    def choose_action(self, game, player_id):
        player = game.players[player_id]
        board = game.board

        # 1. Si c'est le tour du voleur → on le déplace
        if hasattr(game, 'robber_turn') and game.robber_turn:
            best_hex = None
            max_opponents = -1

            for hex_pos in board.get_all_hexes():
                adj = board.get_adjacent_players(hex_pos)
                opponents = len([p for p, _ in adj if p != player_id])
                if opponents > max_opponents:
                    max_opponents = opponents
                    best_hex = hex_pos

            if best_hex:
                return Action('move_robber', best_hex)
            return Action('move_robber', random.choice(board.get_all_hexes()))

        # 2. Priorité : construire une ville si possible (plus de points)
        own_settlements = [
            v for v, (p, t) in board.buildings.items()
            if p == player_id and t == 'settlement'
        ]
        if player.can_build_city() and own_settlements:
            return Action('build_city', random.choice(own_settlements))

        # 3. Puis un village si possible
        free_vertices = [v for v in board.get_all_vertices() if v not in board.buildings]
        if player.can_build_settlement() and free_vertices:
            return Action('build_settlement', random.choice(free_vertices))

        # 4. Puis une route
        possible_roads = board.get_possible_roads(player_id)
        if player.can_build_road() and possible_roads:
            return Action('build_road', random.choice(possible_roads))

        # 5. Sinon on passe
        return Action('pass')

    def choose_trade(self, game, pid):
        """
        Décide si on fait un trade banque (4:1 / 3:1 / 2:1)
        Retourne un dict compatible avec Action ou None
        """
        player = game.players[pid]
        ports = game.board.get_player_ports(pid)

        total = sum(player.resources.values())
        if total < 4:
            return None

        # Ressource la plus abondante
        abundant = max(player.resources, key=player.resources.get)
        if player.resources[abundant] < 4:
            return None

        # Ce qu’on veut recevoir (priorité : ce qu’on a peu)
        candidates = [r for r in RESOURCES if r != abundant and player.resources[r] <= 2]
        if not candidates:
            candidates = [r for r in RESOURCES if r != abundant]

        want = random.choice(candidates)

        ratio = player.can_trade_to_bank(abundant, want, ports)
        if ratio:
            return Action(
                action='trade_bank',
                target={
                    'give': abundant,
                    'give_amount': ratio,
                    'receive': want,
                    'receive_amount': 1
                }
            )

        return None

    def choose_player_trade(self, game, pid):
        """
        Propose un échange avec un autre joueur
        Retourne un dict ou None
        """
        player = game.players[pid]
        others = [p for i, p in enumerate(game.players) if i != pid]

        if sum(player.resources.values()) < 2:
            return None

        # Ce qu'on donne
        give_res = max(player.resources, key=player.resources.get)
        if player.resources[give_res] < 1:
            return None

        # Adversaire cible (random)
        target_player = random.choice(others)

        # Ce qu'on veut recevoir
        candidates = [r for r in RESOURCES if player.resources[r] <= 1 and r != give_res]
        if not candidates:
            candidates = [r for r in RESOURCES if r != give_res]
        receive_res = random.choice(candidates)

        # Quantité donnée (1 ou 2 selon abondance)
        give_amount = 1 if player.resources[give_res] <= 3 else 2

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