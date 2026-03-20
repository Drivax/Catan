import random
from collections import Counter
from agents.base import Agent, Action
from game.rules import RESOURCES, COST_ROAD, COST_SETTLEMENT, COST_CITY
from game.map import get_corners


class SmartAgent(Agent):
    """
    Agent intelligent pour Catan avec comportements configurables:
    - Priorise les villes (gain +1 point immédiat)
    - Villages sur les meilleurs spots (numéros chauds + diversité)
    - Routes pour ouvrir des spots à fort potentiel ou bloquer
    - Voleur : cible les leaders ou les joueurs riches
    - Trades banque/joueurs : configurables
    """

    def __init__(self, prob_trade=0.7, road_maker=0, greed=0):
        """
        Args:
            prob_trade (float): Probabilité de vouloir faire un trade à chaque tour [0-1]
            road_maker (int): 0=normal, 1=maximiser construction de routes
            greed (int): 0=normal, 1=seulement trades avantageux (1 ressource contre 2+)
        """
        super().__init__()
        self.last_upgraded_vertex = None
        self.prob_trade = max(0.0, min(1.0, prob_trade))  # Clamp [0, 1]
        self.road_maker = 1 if road_maker else 0
        self.greed = 1 if greed else 0

    def choose_action(self, game, pid):
        player = game.players[pid]
        board = game.board

        # 1. Robber if triggered
        if hasattr(game, 'robber_turn') and game.robber_turn:
            return self._choose_robber_move(game, pid)

        # Determine priority: road_maker prioritizes routes before settlements
        if self.road_maker:
            # ROAD_MAKER MODE: Build roads aggressively
            possible_roads = board.get_possible_roads(pid)
            if player.can_build_road() and possible_roads:
                best_edge = max(possible_roads, key=lambda e: self._road_value(board, e, pid))
                return Action('build_road', best_edge)

        # 2. UPGRADE TO CITY - but only after 4+ settlements
        own_settlements = [
            v for v, (p, t) in board.buildings.items()
            if p == pid and t == 'settlement' and v != self.last_upgraded_vertex
        ]
        num_settlements = sum(1 for (p, t) in board.buildings.values() if p == pid and t == 'settlement')
        
        if player.can_build_city() and own_settlements and num_settlements >= 4:
            best_v = max(own_settlements, key=lambda v: self._vertex_value(board, v))
            self.last_upgraded_vertex = best_v
            return Action('build_city', best_v)

        # 3. BUILD NEW SETTLEMENT - URGENT PRIORITY (before board fills)
        free_vertices = [v for v in board.get_all_vertices() if v not in board.buildings]
        
        # Get valid settlement spots - must check 1-edge distance (neighbors only)
        valid_settle_spots = []
        for v in free_vertices:
            # Check if any existing settlement is adjacent (in neighbors)
            neighbors = set(board.vertex_neighbors.get(v, []))
            has_adjacent = any(existing in neighbors for existing in board.buildings.keys())
            if not has_adjacent:
                valid_settle_spots.append(v)
        
        # If valid spots exist and we have resources, BUILD IMMEDIATELY
        if player.can_build_settlement() and valid_settle_spots:
            best_v = max(valid_settle_spots, key=lambda v: self._vertex_value(board, v))
            return Action('build_settlement', best_v)
        
        # If we have settlement resources but NO valid spots, build roads
        has_settlement_resources = all(player.resources.get(r, 0) >= 1 for r in ['wood', 'brick', 'sheep', 'wheat'])
        if has_settlement_resources and not valid_settle_spots:
            possible_roads = board.get_possible_roads(pid)
            if player.can_build_road() and possible_roads:
                best_edge = max(possible_roads, key=lambda e: self._road_value(board, e, pid))
                return Action('build_road', best_edge)

        # 4. BUILD ROADS - expand territory for future opportunities
        possible_roads = board.get_possible_roads(pid)
        if player.can_build_road() and possible_roads:
            best_edge = max(possible_roads, key=lambda e: self._road_value(board, e, pid))
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
        """Score vertices aggressively - prioritize RESOURCE DIVERSITY for early game"""
        score = 0.0
        
        # Find all hexes this vertex touches
        resources_present = Counter()
        number_score = 0.0
        
        for hex_pos, tile in board.hexes.items():
            if vertex in get_corners(*hex_pos):
                if tile.resource != 'desert':
                    resources_present[tile.resource] += 1
                if tile.number:
                    # Score for production probability
                    if tile.number in [6, 8]:
                        number_score += 3.0
                    elif tile.number in [5, 9]:
                        number_score += 2.0
                    else:
                        number_score += 1.0
        
        # HEAVILY prioritize resource diversity - EMERGENCY if only touching 1 resource
        diversity = len(resources_present)
        if diversity == 1:
            # Single resource - bonus for settlements, but still score it
            resource_type = list(resources_present.keys())[0]
            if resource_type == 'ore':
                score += 0.1  # Ore is scarce, still valuable
            elif resource_type in ['wheat', 'sheep']:
                score += 0.05  # Medium value
            else:
                score += 0.0  # Brick/wood less critical early
        elif diversity == 2:
            score += number_score + 1.0
        elif diversity == 3:
            # Best possible - 3 different resources
            score += number_score + 5.0
        
        return score

    def _road_value(self, board, edge, player_id):
        """Score roads - in early game accept any connected road; later prioritize good spots"""
        v1, v2 = list(edge)
        score = 0.5  # Base score - all roads have some value for expanding territory
        
        for v in (v1, v2):
            # Major bonus if it connects to our buildings
            if v in board.buildings and board.buildings[v][0] == player_id:
                score += 3.0
            else:
                # Minor score if extends our road network to new territory
                score += 0.3
            
            # Check if it opens access to valuable free vertices
            free_neighbors = [
                nv for nv in board.vertex_neighbors.get(v, [])
                if nv not in board.buildings
            ]
            
            if free_neighbors:
                best_neighbor_value = max(
                    (self._vertex_value(board, nv) for nv in free_neighbors),
                    default=0
                )
                # Bonus for opening good spots
                score += best_neighbor_value * 0.3

        return score

    def choose_trade(self, game, pid):
        """Bank trading - smart conversions for building resources
        Respects prob_trade and greed parameters
        """
        # Check if agent wants to trade this turn (based on prob_trade)
        if random.random() > self.prob_trade:
            return None
            
        player = game.players[pid]
        ports = game.board.get_player_ports(pid)

        total = sum(player.resources.values())
        
        # Already have everything needed? Don't trade
        can_build_settlement = all(player.resources.get(r, 0) >= 1 for r in ['wood', 'brick', 'sheep', 'wheat'])
        can_build_city = player.resources.get('wheat', 0) >= 2 and player.resources.get('ore', 0) >= 3
        
        if can_build_settlement or can_build_city:
            return None
        
        # What do we need to build?
        needs = []
        
        # Check settlement - need 1 of each: wood, brick, sheep, wheat
        missing_settlement = [r for r in ['wood', 'brick', 'sheep', 'wheat']
                             if player.resources.get(r, 0) == 0]
        if missing_settlement and len(missing_settlement) <= 2:  # Only trade if close to complete
            needs.extend(missing_settlement)
        
        # Check city upgrade - need 2 wheat + 3 ore
        if player.resources.get('wheat', 0) < 2:
            needs.append('wheat')
        if player.resources.get('ore', 0) < 3:
            needs.extend(['ore'] * (3 - player.resources.get('ore', 0)))
        
        if not needs:
            return None
        
        # What can we give up? (only abundant resources)
        abundant = [r for r in RESOURCES if player.resources.get(r, 0) >= 3]
        if not abundant:
            return None
        
        # Trade priority: first missing resource that's needed
        want = needs[0]
        give = max(abundant, key=lambda r: player.resources.get(r, 0))
        
        # Check if we can trade at a reasonable ratio
        ratio = player.can_trade_to_bank(give, want, ports)
        if ratio is None:
            return None
            
        # GREED mode: only accept trades that are advantageous (give 1, get 2+)
        if self.greed and ratio >= 1:  # ratio >= 1 means we have to give >=1 (bad deal in greed mode)
            return None
        
        if player.resources.get(give, 0) >= ratio:
            return {
                'give': give,
                'receive': want,
                'ratio': ratio
            }
        
        return None

    def choose_player_trade(self, game, pid):
        """Find mutually beneficial trades - not just overpaying
        Respects prob_trade and greed parameters
        """
        # Check if agent wants to trade this turn (based on prob_trade)
        if random.random() > self.prob_trade:
            return None
            
        player = game.players[pid]
        board = game.board
        
        # What do we need?
        settlement_needs = [r for r in ['wood', 'brick', 'sheep', 'wheat']
                           if player.resources.get(r, 0) == 0]
        city_needs = []
        if player.resources.get('wheat', 0) < 2:
            city_needs.append('wheat')
        if player.resources.get('ore', 0) < 3:
            for _ in range(3 - player.resources.get('ore', 0)):
                city_needs.append('ore')
        
        needs = settlement_needs if settlement_needs else city_needs
        if not needs:
            return None
        
        want = needs[0]  # What we want most
        
        # What do we have excess of? (not what we need)
        abundant = [r for r in RESOURCES 
                   if player.resources.get(r, 0) >= 2 and r != want]
        
        if not abundant:
            return None
        
        # Find opponent who wants what we have AND has what we need
        best_trade = None
        best_score = -1
        
        for opponent_id in range(len(game.players)):
            if opponent_id == pid:
                continue
            
            opponent = game.players[opponent_id]
            
            # Does opponent have what we want?
            if opponent.resources.get(want, 0) == 0:
                continue
            
            # Find what opponent might want from us
            opp_settlements = [v for v, (p, t) in board.buildings.items()
                             if p == opponent_id and t == 'settlement']
            opp_cities = [v for v, (p, t) in board.buildings.items()
                         if p == opponent_id and t == 'city']
            
            # What does opponent need?
            opp_settlement_needs = [r for r in ['wood', 'brick', 'sheep', 'wheat']
                                   if opponent.resources.get(r, 0) == 0]
            opp_city_needs = []
            if opponent.resources.get('wheat', 0) < 2:
                opp_city_needs.append('wheat')
            if opponent.resources.get('ore', 0) < 3:
                opp_city_needs.append('ore')
            
            opp_needs = opp_settlement_needs if opp_settlement_needs else opp_city_needs
            
            # Look for trades where we both benefit
            for give_res in abundant:
                # Does opponent want what we offer?
                if give_res in opp_needs:
                    # This is a good trade! They get what they need, we get what we need
                    # Fair ratio: 1:1 if it helps both build
                    trade_score = 10  # High priority - mutual benefit
                    ratio = 1
                    
                    if trade_score > best_score:
                        best_score = trade_score
                        best_trade = {
                            'opponent': opponent_id,
                            'give': give_res,
                            'want': want,
                            'ratio': ratio
                        }
                
                # GREED mode: only unfavorable trades to opponent (give 1, get 1 is fair, we want 2+:1)
                # In non-greed: allow slightly unfavorable trades (2:1)
                elif opponent.resources.get(give_res, 0) == 0 and give_res not in opp_needs:
                    if not self.greed:  # Only in non-greed mode
                        # We give abundant resource, they give what we need
                        # Slightly favorable to us, but still reasonable
                        trade_score = 5
                        ratio = 2  # 2:1 - slightly worse for them but still helps
                        
                        if trade_score > best_score:
                            best_score = trade_score
                            best_trade = {
                                'opponent': opponent_id,
                                'give': give_res,
                                'want': want,
                                'ratio': ratio
                            }
        
        if best_trade:
            give_res = best_trade['give']
            want_res = best_trade['want']
            ratio = best_trade['ratio']
            
            if player.resources.get(give_res, 0) >= ratio:
                return Action(
                    action='trade_player_offer',
                    target={
                        'target_pid': best_trade['opponent'],
                        'give_res': give_res,
                        'give_amount': ratio,
                        'receive_res': want_res,
                        'receive_amount': 1
                    }
                )
        
        return None