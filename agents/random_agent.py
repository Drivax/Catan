import random
from agents.base import Agent,Action
from game.rules import RESOURCES

class RandomAgent(Agent):
    def choose_action(self, game, player_id):
        player = game.players[player_id]
        board = game.board

        free_verts = [v for v in board.get_all_vertices() if v not in board.buildings]
        if player.can_build_settlement() and free_verts:
            return Action('build_settlement', random.choice(free_verts))

        own_setts = [v for v, (p, t) in board.buildings.items() if p == player_id and t == 'settlement']
        if player.can_build_city() and own_setts:
            return Action('build_city', random.choice(own_setts))

        poss_roads = board.get_possible_roads(player_id)
        if player.can_build_road() and poss_roads:
            return Action('build_road', random.choice(poss_roads))

        if hasattr(game, 'robber_turn') and game.robber_turn:
                board = game.board
                best_hex = None
                max_opponents = 0
                
                for hex_pos in board.get_all_hexes():
                    adj_players = board.get_adjacent_players(hex_pos)
                    opponent_count = len([p for p, _ in adj_players if p != player_id])
                    if opponent_count > max_opponents:
                        max_opponents = opponent_count
                        best_hex = hex_pos
                
                if best_hex:
                    return Action('move_robber', best_hex)
                return Action('move_robber', random.choice(board.get_all_hexes()))  # fallback
        return Action('pass')
    

    def choose_trade(self, game, pid):
        player = game.players[pid]
        ports = game.board.get_player_ports(pid)
        
        total_res = sum(player.resources.values())
        if total_res < 4:
            return None
        
        abundant = max(player.resources, key=player.resources.get)
        if player.resources[abundant] < 4:
            return None
        
        candidates = []
        for r in RESOURCES:
            if r != abundant and player.resources[r] <= 2: 
                candidates.append(r)
        
        if not candidates:
            candidates = [r for r in RESOURCES if r != abundant]
        
        want = random.choice(candidates)
        
        ratio = player.can_trade_to_bank(abundant, want, ports)
        if ratio:
            return {
                'action': 'trade_bank',
                'give': abundant,
                'receive': want,
                'ratio': ratio
            }
        
        return None
    def choose_trade(self, game, pid):
            player = game.players[pid]
            ports = game.board.get_player_ports(pid)
            
            if sum(player.resources.values()) < 4:
                return None
            
            abundant = max(player.resources, key=player.resources.get)
            if player.resources[abundant] < 4:
                return None
            
            want = random.choice([r for r in RESOURCES if r != abundant])
            ratio = player.can_trade_to_bank(abundant, want, ports)
            
            if ratio:
                return {'give': abundant, 'receive': want, 'ratio': ratio}
            return None