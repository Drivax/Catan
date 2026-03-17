# agents/smart_agent.py
import random
from collections import Counter
from agents.base import Agent, Action
from game.rules import RESOURCES, COST_ROAD, COST_SETTLEMENT, COST_CITY
from game.map import get_corners


class SmartAgent(Agent):
    """
    Agent intelligent pour Catan :
    - Priorise les villes (gain +1 point immédiat)
    - Villages sur les meilleurs spots (numéros chauds + diversité)
    - Routes pour ouvrir des spots à fort potentiel ou bloquer
    - Voleur : cible les leaders ou les joueurs riches
    - Trades banque : seulement quand excès clair et besoin réel
    - Trades joueurs : rares et seulement très avantageux
    """

    def __init__(self):
        super().__init__()
        # Petite mémoire pour éviter de toujours upgrader le même settlement
        self.last_upgraded_vertex = None

    def choose_action(self, game, pid):
        player = game.players[pid]
        board = game.board

        # 1. Priorité absolue : voleur si c'est le tour du voleur
        if hasattr(game, 'robber_turn') and game.robber_turn:
            return self._choose_robber_move(game, pid)

        # 2. AGGRESSIVE: Construire une ville si possible (gain +1 point = +10% vers la victoire)
        own_settlements = [
            v for v, (p, t) in board.buildings.items()
            if p == pid and t == 'settlement' and v != self.last_upgraded_vertex
        ]
        if player.can_build_city() and own_settlements:
            best_v = max(own_settlements, key=lambda v: self._vertex_value(board, v))
            self.last_upgraded_vertex = best_v
            return Action('build_city', best_v)

        # 3. AGGRESSIVE: Nouveau village sur le meilleur spot disponible
        free_vertices = [v for v in board.get_all_vertices() if v not in board.buildings]
        if player.can_build_settlement() and free_vertices:
            best_v = max(free_vertices, key=lambda v: self._vertex_value(board, v))
            return Action('build_settlement', best_v)

        # 4. Route : seulement si on have clear path to unbuilt spot
        possible_roads = board.get_possible_roads(pid)
        if player.can_build_road() and possible_roads:
            # Only build roads that lead to good expansion spots
            good_roads = [
                e for e in possible_roads 
                if self._road_value(board, e, pid) > 2.0  # Higher threshold
            ]
            if good_roads:
                best_edge = max(good_roads, key=lambda e: self._road_value(board, e, pid))
                return Action('build_road', best_edge)

        return Action('pass')

    def _choose_robber_move(self, game, pid):
        """AGGRESSIVE robber blocking - prioritize leader"""
        board = game.board
        player = game.players[pid]
        
        # Find the leader
        leader_pid = max(range(game.num_players), key=lambda i: game.players[i].victory_points)
        
        best_hex = None
        best_score = -1

        for hex_pos in board.get_all_hexes():
            adj = board.get_adjacent_players(hex_pos)
            
            score = 0
            for opp_pid, _ in adj:
                if opp_pid == pid:
                    continue
                    
                opp = game.players[opp_pid]
                
                # HEAVILY prioritize blocking the leader
                if opp_pid == leader_pid:
                    score += opp.victory_points * 20  # Huge multiplier for leader
                else:
                    score += opp.victory_points * 3
                
                # Add resource penalty
                score += sum(opp.resources.values())
                
                # Bonus for buildings adjacent
                adj_buildings = sum(1 for v, (p, _) in board.buildings.items() 
                                  if p == opp_pid and v in get_corners(*hex_pos))
                score += adj_buildings * 5

            if score > best_score:
                best_score = score
                best_hex = hex_pos

        if best_hex and best_score > 0:
            return Action('move_robber', best_hex)

        # Fallback: random hex with opponents
        hexes_with_opp = [
            h for h in board.get_all_hexes()
            if any(p != pid for p, _ in board.get_adjacent_players(h))
        ]
        
        if hexes_with_opp:
            return Action('move_robber', random.choice(hexes_with_opp))
        
        return Action('move_robber', random.choice(board.get_all_hexes()))

    def _vertex_value(self, board, vertex):
        """Aggressively score vertices - weight best production heavily"""
        score = 0.0

        for hex_pos, tile in board.hexes.items():
            if vertex in get_corners(*hex_pos):
                if tile.number:
                    # Extreme weights for best numbers (6, 8 appear most frequently)
                    val_map = {
                        6: 5.0,   # Most common
                        8: 5.0,
                        5: 3.5,   # Good
                        9: 3.5,
                        4: 2.0,   # Decent
                        10: 2.0,
                        3: 1.0,   # Poor
                        11: 1.0,
                        2: 0.3,   # Rare
                        12: 0.3
                    }
                    score += val_map.get(tile.number, 0.0)

        # Heavy bonus for resource diversity (settlement produces multiple resources)
        resources_present = set()
        for hex_pos, tile in board.hexes.items():
            if vertex in get_corners(*hex_pos) and tile.resource != 'desert':
                resources_present.add(tile.resource)
        
        # Quadratic bonus for diversity (3 resources = 2x better than 1)
        diversity_bonus = len(resources_present) ** 1.5
        score += diversity_bonus

        return score

    def _road_value(self, board, edge, player_id):
        """Only build roads that open HIGH-VALUE settlement spots"""
        v1, v2 = list(edge)
        score = 0.0

        for v in (v1, v2):
            # Must connect to our buildings
            if v in board.buildings and board.buildings[v][0] == player_id:
                score += 5.0
            else:
                # Only minor score if it connects to our road network
                score += 0.5

            # Check if it opens access to a valuable free vertex
            free_neighbors = [
                nv for nv in board.vertex_neighbors.get(v, [])
                if nv not in board.buildings
            ]
            
            if free_neighbors:
                best_neighbor_value = max(
                    (self._vertex_value(board, nv) for nv in free_neighbors),
                    default=0
                )
                # Must open to a GOOD spot
                if best_neighbor_value > 3.0:
                    score += best_neighbor_value * 1.5
            
            # Small bonus for blocking opponents (only if opening to good spot)
            for nv in board.vertex_neighbors.get(v, []):
                if nv in board.buildings and board.buildings[nv][0] != player_id:
                    score += 1.0

        return score

    def choose_trade(self, game, pid):
        """AGGRESSIVE bank trading to get resources for building"""
        player = game.players[pid]
        ports = game.board.get_player_ports(pid)

        total = sum(player.resources.values())
        
        # What do we need for next building action?
        need_settlement = not all(player.resources.get(r, 0) >= 1 for r in ['wood', 'brick', 'sheep', 'wheat'])
        need_city = player.resources.get('wheat', 0) < 2 or player.resources.get('ore', 0) < 3
        need_road = not all(player.resources.get(r, 0) >= 1 for r in ['wood', 'brick'])

        # Identify what we're missing (lowest resource that we need)
        missing = []
        if need_settlement or need_city or need_road:
            for r in RESOURCES:
                current = player.resources.get(r, 0)
                if (need_settlement and r in ['wood', 'brick', 'sheep', 'wheat'] and current < 1) or \
                   (need_city and r == 'wheat' and current < 2) or \
                   (need_city and r == 'ore' and current < 3) or \
                   (need_road and r in ['wood', 'brick'] and current < 1):
                    missing.append((r, current))

        if not missing:
            return None

        # Find what we have in excess
        want_resource = min(missing, key=lambda x: x[1])[0]  # Most scarce of what we need
        
        # Find abundant resource we can trade
        abundant_options = [(r, player.resources.get(r, 0)) for r in RESOURCES 
                           if player.resources.get(r, 0) >= 2 and r != want_resource]
        
        if not abundant_options:
            return None

        give_resource = max(abundant_options, key=lambda x: x[1])[0]

        ratio = player.can_trade_to_bank(give_resource, want_resource, ports)
        if ratio is None:
            return None

        # More aggressive: trade even at 4:1 if we need it badly
        if player.resources[give_resource] >= ratio:
            return {
                'give': give_resource,
                'receive': want_resource,
                'ratio': ratio
            }
        return None

    def choose_player_trade(self, game, pid):
        """AGGRESSIVE: Always look for trades to complete buildings"""
        player = game.players[pid]
        
        # Analyze what we need to build next
        need_settlement = [r for r in ['wood', 'brick', 'sheep', 'wheat'] if player.resources.get(r, 0) == 0]
        need_city = []
        if player.resources.get('wheat', 0) < 2:
            need_city.append('wheat')
        if player.resources.get('ore', 0) < 3:
            need_city.extend(['ore'] * (3 - player.resources.get('ore', 0)))

        # Prioritize completing settlements (faster to build)
        critical_needs = need_settlement if need_settlement else need_city

        if critical_needs:
            needed = critical_needs[0]
            
            # Find a player with what we need
            best_trade = None
            best_score = -1
            
            for other in [p for i, p in enumerate(game.players) if i != pid]:
                if other.resources.get(needed, 0) >= 1:
                    # What can we give them?
                    giveable = [r for r in RESOURCES if player.resources.get(r, 0) >= 2 and r != needed]
                    if giveable:
                        give_res = max(giveable, key=lambda r: player.resources.get(r, 0))
                        
                        # Score: how much they need what we're giving
                        other_needs = [r for r in RESOURCES if other.resources.get(r, 0) <= 1]
                        score = 1 if give_res in other_needs else 0
                        score += other.resources.get(needed, 0)  # More valuable if they have more
                        
                        if score > best_score:
                            best_score = score
                            best_trade = (other.pid, give_res, needed)
            
            if best_trade:
                target_pid, give_res, receive_res = best_trade
                give_amount = min(2, player.resources.get(give_res, 0) // 2)
                return Action(
                    action='trade_player_offer',
                    target={
                        'target_pid': target_pid,
                        'give_res': give_res,
                        'give_amount': max(1, give_amount),
                        'receive_res': receive_res,
                        'receive_amount': 1
                    }
                )

        # Opportunistic trading: clear excess
        abundant = max([r for r in RESOURCES], key=lambda r: player.resources.get(r, 0))
        if player.resources.get(abundant, 0) >= 3:
            scarce = min([r for r in RESOURCES], key=lambda r: player.resources.get(r, 0))
            if scarce != abundant and player.resources.get(scarce, 0) < 2:
                for other in [p for i, p in enumerate(game.players) if i != pid]:
                    if other.resources.get(scarce, 0) >= 1:
                        return Action(
                            action='trade_player_offer',
                            target={
                                'target_pid': other.pid,
                                'give_res': abundant,
                                'give_amount': 2,
                                'receive_res': scarce,
                                'receive_amount': 1
                            }
                        )

        return None