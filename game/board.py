# Tiles coordinates, intersections...

import random
from collections import Counter, defaultdict
from game.map import HEX_POSITIONS, get_corners,PORTS
from game.rules import RESOURCES

HEX_RESOURCES_DISTRIB = (
    ["wood"]*4 + ["brick"]*3 + ["sheep"]*4 +
    ["wheat"]*4 + ["ore"]*3 + ["desert"]
)


HEX_NUMBERS_DISTRIB = [2,3,3,4,4,5,5,6,6,8,8,9,9,10,10,11,11,12]

class HexTile:
    def __init__(self, resource, number=None):
        self.resource = resource
        self.number = number
        self.robber = resource == "desert"

class Board:
    def __init__(self):
        # Shuffle tiles et numbers
        tiles_resources = list(HEX_RESOURCES_DISTRIB)
        numbers = HEX_NUMBERS_DISTRIB
        random.shuffle(tiles_resources)
        random.shuffle(numbers)
        num_idx = 0

        self.hexes = {}
        for pos in HEX_POSITIONS:
            res = tiles_resources.pop(0)
            number = None if res == "desert" else numbers[num_idx]
            if res != "desert":
                num_idx += 1
            self.hexes[pos] = HexTile(res, number)

        # Robber on désert
        self.robber_pos = next(pos for pos, tile in self.hexes.items() if tile.robber)

        # Bâtiments : vertex_key -> (player_id, 'settlement' or 'city')
        self.buildings = {}

        # Precompute pour perf (optionnel)
        self.production_map = defaultdict(list)
        for pos, tile in self.hexes.items():
            if tile.number:
                self.production_map[tile.number].append(pos)

        # Création des edges et voisins
        self.all_edges = set()
        self.vertex_neighbors = defaultdict(list)
        self.roads = {} 

        for hex_pos in self.hexes:
            corners = get_corners(*hex_pos)
            for i in range(6):
                v1 = corners[i]
                v2 = corners[(i + 1) % 6]
                edge = frozenset({v1, v2})
                self.all_edges.add(edge)

                self.vertex_neighbors[v1].append(v2)
                self.vertex_neighbors[v2].append(v1)

        for v in self.vertex_neighbors:
            self.vertex_neighbors[v] = list(set(self.vertex_neighbors[v]))

        # print(f"number unique edges : {len(self.all_edges)}") 

        self.ports=[]

        for v1,v2 in PORTS:
            edge=frozenset({v1,v2})
            if edge not in self.all_edges:
                print(f"error with the port {v1}-{v2}")
                continue
            port_types=['generic']*4 +['wood','brick','sheep','wheat','ore']
            random.shuffle(port_types)
            port_type=port_types.pop()
            self.ports.append({
                'edge': edge,
                'type': port_type,
                'vertices': (v1, v2)
            })

        # verification
        # all_corners = set()
        # for pos in self.hexes:
        #     all_corners.update(get_corners(*pos))
        # print(f"Unique vertex : {len(all_corners)}")  # around 54
        # print("Exemples :", sorted(list(all_corners))[:10], "... et", sorted(list(all_corners))[-10:])

    def get_all_vertices(self):
        vertices = set()
        for pos in self.hexes:
            vertices.update(get_corners(*pos))
        return list(vertices)  # ~54 uniques
    
    def approx_distance(self, v1, v2):
        q1, r1 = v1
        q2, r2 = v2
        return max(abs(q1 - q2), abs(r1 - r2), abs((q1 + r1) - (q2 + r2))) // 2
    
    def place_road(self,pid,edge):
        if edge in self.roads:
            return False
        if edge not in self.all_edges:
            return False
        v1,v2=list(edge)
        adjacent=False
        if v1 in self.buildings and self.buildings[v1][0] == pid:
            adjacent = True
        if v2 in self.buildings and self.buildings[v2][0] == pid:
            adjacent = True
        for e, p in self.roads.items():
            if p == pid and (v1 in e or v2 in e):
                adjacent = True
                break
        if not adjacent:
            return False
        self.roads[edge] = pid
        return True

    def get_possible_roads(self, pid):
        own_vertices = set()

        for v, (p, _) in self.buildings.items():
            if p == pid:
                own_vertices.add(v)

        for edge, p in self.roads.items():
            if p == pid:
                own_vertices.update(edge)

        possible = []
        for v in own_vertices:
            for nv in self.vertex_neighbors[v]:
                edge = frozenset({v, nv})
                if edge not in self.roads:
                    possible.append(edge)
        return list(set(possible)) 

    def get_longest_road_length(self, pid):
        graph = defaultdict(list)
        for edge, p in self.roads.items():
            if p == pid:
                v1, v2 = list(edge)
                graph[v1].append(v2)
                graph[v2].append(v1)
        if not graph:
            return 0

        def dfs(curr, visited):
            max_len = 0
            for neigh in graph[curr]:
                if neigh not in visited:
                    visited.add(neigh)
                    max_len = max(max_len, 1 + dfs(neigh, visited))
                    visited.remove(neigh)
            return max_len

        max_path = 0
        for start in list(graph):
            visited = set([start])
            max_path = max(max_path, dfs(start, visited))
        return max_path

    def place_settlement(self, pid, vkey):
        if vkey in self.buildings:
            return False
    
        for existing_v, (existing_pid, btype) in self.buildings.items():
            dist = self.approx_distance(vkey, existing_v)
            if dist < 2:
                return False
            
        self.buildings[vkey] = (pid, 'settlement')
        return True

    def upgrade_to_city(self, pid, vkey):
        if vkey in self.buildings and self.buildings[vkey] == (pid, 'settlement'):
            self.buildings[vkey] = (pid, 'city')
            return True
        return False

    def move_robber(self, new_pos):
        self.robber_pos = new_pos

    def produce(self, dice_value):
        produced = defaultdict(Counter)
        if dice_value == 7:
            return produced
        for hex_pos in self.production_map.get(dice_value, []):
            if hex_pos == self.robber_pos:
                continue
            tile = self.hexes[hex_pos]
            for vkey in get_corners(*hex_pos):
                if vkey in self.buildings:
                    pid, btype = self.buildings[vkey]
                    amt = 2 if btype == 'city' else 1
                    produced[pid][tile.resource] += amt
                    print(f"  +{amt} {tile.resource} → J{pid} (vertex {vkey}, hex {hex_pos})")
        return produced
    
    def get_adjacent_players(self, hex_pos):
        adjacent = []
        corners = get_corners(*hex_pos)
        for vkey in corners:
            if vkey in self.buildings:
                pid, btype = self.buildings[vkey]
                adjacent.append((pid, btype))
        return adjacent  

    def get_all_hexes(self):
        return list(self.hexes.keys())

    def get_steal_candidates(self, hex_pos, exclude_pid):

        candidates = []
        for pid, _ in self.get_adjacent_players(hex_pos):
            if pid != exclude_pid:
                candidates.append(pid)
        return candidates
    
    def get_player_ports(self,player_id):
        accessible=set()
        for port in self.ports:
            v1,v2=port['vertices']
            if (v1 in self.buildings and self.buildings[v1][0] == player_id) or(v2 in self.buildings and self.buildings[v2][0] == player_id):
                accessible.add(port['type'])
        return accessible