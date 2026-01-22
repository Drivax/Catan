# Tiles coordinates, intersections...

import random
from collections import Counter, defaultdict
from game.map import HEX_POSITIONS, get_corners,PORTS
from game.rules import RESOURCES
import math

HEX_RESOURCES_DISTRIB = (
    ["wood"]*4 + ["brick"]*3 + ["sheep"]*4 +
    ["wheat"]*4 + ["ore"]*3 + ["desert"]
)


HEX_NUMBERS_DISTRIB = [2,3,3,4,4,5,5,6,6,8,8,9,9,10,10,11,11,12]

HEX_RADIUS = 70                
HEX_WIDTH = HEX_RADIUS * 2
HEX_HEIGHT = HEX_RADIUS * math.sqrt(3)
HEX_INNER_RADIUS = HEX_RADIUS * math.sqrt(3) / 2   

COLORS = {
    'desert': (210, 180, 140),
    'wood':   (34, 139, 34),
    'brick':  (165, 42, 42),
    'sheep':  (144, 238, 144),
    'wheat':  (255, 215, 0),
    'ore':    (105, 105, 105),
    'water':  (100, 149, 237),
}
PLAYER_COLORS = [
    (220, 20, 60),     # J0 - rouge vif
    (30, 144, 255),    # J1 - bleu
    (255, 215, 0),     # J2 - jaune/or
    (50, 205, 50),     # J3 - vert lime
]

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
        self.hex_centers = {}          
        self.hex_polygons = {}      

        for pos in HEX_POSITIONS:
            res = tiles_resources.pop(0)
            number = None if res == "desert" else numbers[num_idx]
            if res != "desert":
                num_idx += 1
            self.hexes[pos] = HexTile(res, number)

            cx, cy = self.axial_to_pixel(*pos)
            self.hex_centers[pos] = (cx, cy)
            self.hex_polygons[pos] = self.get_hex_points(cx, cy)

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
        self.buildings = {}
        self.production_map = defaultdict(list)
        for pos, tile in self.hexes.items():
            if tile.number:
                self.production_map[tile.number].append(pos)

        self.ports = []

        edge_hex_count = defaultdict(int)
        for hex_pos in self.hexes:
            corners = get_corners(*hex_pos)
            for i in range(6):
                v1 = corners[i]
                v2 = corners[(i + 1) % 6]
                edge = frozenset({v1, v2})
                edge_hex_count[edge] += 1

        border_edges = [edge for edge, count in edge_hex_count.items() if count == 1]

        random.shuffle(border_edges)
        border_edges = border_edges[:9]  

        port_types = ['generic'] * 4 + ['wood', 'brick', 'sheep', 'wheat', 'ore']
        random.shuffle(port_types)

        for i, edge in enumerate(border_edges):
            v1, v2 = list(edge)
            ptype = port_types[i]

            px1, py1 = self.vertex_to_pixel(*v1)
            px2, py2 = self.vertex_to_pixel(*v2)
            center = ((px1 + px2) / 2, (py1 + py2) / 2)

            self.ports.append({
                'edge': edge,
                'type': ptype,
                'vertices': (v1, v2),
                'center': center
            })


        # verification
        # all_corners = set()
        # for pos in self.hexes:
        #     all_corners.update(get_corners(*pos))
        # print(f"Unique vertex : {len(all_corners)}")  # around 54
        # print("Exemples :", sorted(list(all_corners))[:10], "... et", sorted(list(all_corners))[-10:])


    def axial_to_pixel(self, q, r):
        x = HEX_RADIUS * (3/2 * q)
        y = HEX_RADIUS * (math.sqrt(3)/2 * q + math.sqrt(3) * r)
        
        # Centrage du plateau (ajuste ces valeurs !)
        offset_x = 600
        offset_y = 500          # ← souvent plus haut que large
        return x + offset_x, y + offset_y

    def vertex_to_pixel(self, vq, vr):

        q = vq / 2.0  
        r = vr / 2.0
        x = HEX_RADIUS * (3/2 * q)
        y = HEX_RADIUS * math.sqrt(3) * (r + q/2.0)
        
        return x + 600, y + 450
    def get_hex_polygon_points(self, center_x, center_y):
        points = []
        for i in range(6):
            angle_deg = 60 * i + 30   # 30° pour flat-top
            angle_rad = math.radians(angle_deg)
            px = center_x + HEX_RADIUS * math.cos(angle_rad)
            py = center_y + HEX_RADIUS * math.sin(angle_rad)
            points.append((px, py))
        return points
    def get_hex_points(self, center_x, center_y):
        points = []
        for i in range(6):
            angle_deg = 60 * i + 30   # flat-top
            angle_rad = math.radians(angle_deg)
            px = center_x + HEX_RADIUS * math.cos(angle_rad)
            py = center_y + HEX_RADIUS * math.sin(angle_rad)
            points.append((px, py))
        return points
    
    def get_render_data(self):
        return {
            'hex_centers': self.hex_centers,
            'hex_polygons': self.hex_polygons,
            'hex_tiles': self.hexes,
            'robber_pos': self.robber_pos,
            'buildings': self.buildings,
            'roads': self.roads,
            'ports': self.ports,
            'vertex_to_pixel': self.vertex_to_pixel,
        }
    
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
    def produce_from_vertex(self, vkey):
        produced = Counter()
        adjacent_hexes = []
        for hex_pos, tile in self.hexes.items():
            corners = get_corners(*hex_pos)
            if vkey in corners:
                adjacent_hexes.append((hex_pos, tile))
        
        for hex_pos, tile in adjacent_hexes:
            if tile.number is None: 
                continue
            produced[tile.resource] += 1
        
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