import random

from collections import Counter, defaultdict

from game.map import HEX_POSITIONS, get_corners, PORTS

from game.rules import RESOURCES

import math

 

HEX_RESOURCES_DISTRIB = (

    ["wood"] * 4 + ["brick"] * 3 + ["sheep"] * 4 +

    ["wheat"] * 4 + ["ore"] * 3 + ["desert"]

)

HEX_NUMBERS_DISTRIB = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]

 

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

    (220, 20, 60),    # J0 - rouge vif

    (30, 144, 255),   # J1 - bleu

    (255, 215, 0),    # J2 - jaune/or

    (50, 205, 50),    # J3 - vert lime

]

 

OFFSET_X = 600

OFFSET_Y = 500

 

class HexTile:

    def __init__(self, resource, number=None):

        self.resource = resource

        self.number = number

        self.robber = resource == "desert"

 

class Board:

    def __init__(self, verbose=True):

        tiles_resources = list(HEX_RESOURCES_DISTRIB)

        numbers = list(HEX_NUMBERS_DISTRIB)

        self.verbose = verbose

        random.shuffle(tiles_resources)

        random.shuffle(numbers)

 

        num_idx = 0

        self.hexes = {}

        self.hex_centers = {}

        self.hex_polygons = {}

 

        for pos in HEX_POSITIONS:

            res = tiles_resources.pop(0)

            number = None

            if res != "desert":

                number = numbers[num_idx]

                num_idx += 1

            self.hexes[pos] = HexTile(res, number)

            cx, cy = self.axial_to_pixel(*pos)

            self.hex_centers[pos] = (cx, cy)

            self.hex_polygons[pos] = self._compute_hex_points(cx, cy)

 

        # Robber sur le desert

        self.robber_pos = next(pos for pos, tile in self.hexes.items() if tile.robber)

 

        # Batiments : vertex_key -> (player_id, 'settlement' or 'city')

        self.buildings = {}

 

        # Routes : frozenset{v1, v2} -> player_id

        self.roads = {}

 

        # Production map : dice_value -> [hex_pos]

        self.production_map = defaultdict(list)

        for pos, tile in self.hexes.items():

            if tile.number:

                self.production_map[tile.number].append(pos)

 

        # Edges et voisins de vertices

        self.all_edges = set()

        self.vertex_neighbors = defaultdict(set)

 

        for hex_pos in self.hexes:

            corners = get_corners(*hex_pos)

            for i in range(6):

                v1 = corners[i]

                v2 = corners[(i + 1) % 6]

                edge = frozenset({v1, v2})

                self.all_edges.add(edge)

                self.vertex_neighbors[v1].add(v2)

                self.vertex_neighbors[v2].add(v1)

 

        # Convertir en listes pour compatibilite

        self.vertex_neighbors = {v: list(neighbors) for v, neighbors in self.vertex_neighbors.items()}

 

        # Ports sur les aretes de bordure

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

 

    # -------------------------------------------------------------------------

    # Coordonnees

    # -------------------------------------------------------------------------

 

    def axial_to_pixel(self, q, r):

        x = HEX_RADIUS * (3 / 2 * q)

        y = HEX_RADIUS * (math.sqrt(3) / 2 * q + math.sqrt(3) * r)

        return x + OFFSET_X, y + OFFSET_Y

 

    def vertex_to_pixel(self, vq, vr):

        """Convertit des coordonnees de vertex (double-coord) en pixels."""

        q = vq / 2.0

        r = vr / 2.0

        x = HEX_RADIUS * (3 / 2 * q)

        y = HEX_RADIUS * math.sqrt(3) * (r + q / 2.0)

        # FIX: utiliser le meme offset que axial_to_pixel pour l'alignement

        return x + OFFSET_X, y + OFFSET_Y

 

    def _compute_hex_points(self, center_x, center_y):

        """Calcule les 6 sommets d'un hexagone flat-top."""

        points = []

        for i in range(6):

            angle_rad = math.radians(60 * i + 30)

            px = center_x + HEX_RADIUS * math.cos(angle_rad)

            py = center_y + HEX_RADIUS * math.sin(angle_rad)

            points.append((px, py))

        return points

 

    # get_hex_points conserve pour compatibilite ascendante

    def get_hex_points(self, center_x, center_y):

        return self._compute_hex_points(center_x, center_y)

 

    # -------------------------------------------------------------------------

    # Rendu

    # -------------------------------------------------------------------------

 

    def get_render_data(self):

        return {

            'hex_centers':    self.hex_centers,

            'hex_polygons':   self.hex_polygons,

            'hex_tiles':      self.hexes,

            'robber_pos':     self.robber_pos,

            'buildings':      self.buildings,

            'roads':          self.roads,

            'ports':          self.ports,

            'vertex_to_pixel': self.vertex_to_pixel,

        }

 

    # -------------------------------------------------------------------------

    # Vertices / Edges

    # -------------------------------------------------------------------------

 

    def get_all_vertices(self):

        vertices = set()

        for pos in self.hexes:

            vertices.update(get_corners(*pos))

        return list(vertices)

 

    def approx_distance(self, v1, v2):

        q1, r1 = v1

        q2, r2 = v2

        return max(abs(q1 - q2), abs(r1 - r2), abs((q1 + r1) - (q2 + r2))) // 2

 

    # -------------------------------------------------------------------------

    # Construction

    # -------------------------------------------------------------------------

 

    def place_road(self, pid, edge):

        if edge in self.roads:

            return False

        if edge not in self.all_edges:

            return False

        v1, v2 = list(edge)

        adjacent = False

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

        possible = set()

        for v in own_vertices:

            for nv in self.vertex_neighbors.get(v, []):

                edge = frozenset({v, nv})

                if edge not in self.roads:

                    possible.add(edge)

        return list(possible)

 

    def get_longest_road_length(self, pid):

        """

        Calcule la longueur de la plus longue route d'un joueur.

        FIX: compte les aretes (transitions), pas les noeuds.

        """

        # Construire le graphe des aretes du joueur

        edge_list = []

        adj = defaultdict(list)

        for edge, p in self.roads.items():

            if p == pid:

                v1, v2 = list(edge)

                adj[v1].append(v2)

                adj[v2].append(v1)

                edge_list.append(edge)

 

        if not edge_list:

            return 0

 

        def dfs(curr, prev_edge, visited_edges):

            max_len = 0

            for neighbor in adj[curr]:

                edge = frozenset({curr, neighbor})

                if edge not in visited_edges:

                    visited_edges.add(edge)

                    length = 1 + dfs(neighbor, edge, visited_edges)

                    max_len = max(max_len, length)

                    visited_edges.remove(edge)

            return max_len

 

        max_path = 0

        for edge in edge_list:

            v1, v2 = list(edge)

            visited = {edge}

            max_path = max(max_path, 1 + dfs(v2, edge, visited))

            visited = {edge}

            max_path = max(max_path, 1 + dfs(v1, edge, visited))

 

        return max_path

 

    def place_settlement(self, pid, vkey):

        if vkey in self.buildings:

            return False

        # Check 2-edge distance rule: can't have settlements on adjacent vertices
        # Get all neighbors of vkey (1 edge away)
        neighbors = set(self.vertex_neighbors.get(vkey, []))
        
        for existing_v in self.buildings:
            # Reject if existing is on same vertex (impossible but safe)
            if existing_v == vkey:
                return False
            # Reject if existing is adjacent (1 edge away)
            if existing_v in neighbors:
                return False

        self.buildings[vkey] = (pid, 'settlement')

        return True

 

    def upgrade_to_city(self, pid, vkey):

        if vkey in self.buildings and self.buildings[vkey] == (pid, 'settlement'):

            self.buildings[vkey] = (pid, 'city')

            return True

        return False

 

    # -------------------------------------------------------------------------

    # Voleur

    # -------------------------------------------------------------------------

 

    def move_robber(self, new_pos):

        self.robber_pos = new_pos

 

    # -------------------------------------------------------------------------

    # Production

    # -------------------------------------------------------------------------

 

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

                    if self.verbose:
                        print(f"  +{amt} {tile.resource} -> J{pid} (vertex {vkey}, hex {hex_pos})")

        return produced

 

    def produce_from_vertex(self, vkey):

        produced = Counter()

        for hex_pos, tile in self.hexes.items():

            corners = get_corners(*hex_pos)

            if vkey in corners and tile.number is not None:

                produced[tile.resource] += 1

        return produced

 

    # -------------------------------------------------------------------------

    # Utilitaires

    # -------------------------------------------------------------------------

 

    def get_adjacent_players(self, hex_pos):

        adjacent = []

        for vkey in get_corners(*hex_pos):

            if vkey in self.buildings:

                pid, btype = self.buildings[vkey]

                adjacent.append((pid, btype))

        return adjacent

 

    def get_all_hexes(self):

        return list(self.hexes.keys())

 

    def get_steal_candidates(self, hex_pos, exclude_pid):

        return [

            pid for pid, _ in self.get_adjacent_players(hex_pos)

            if pid != exclude_pid

        ]

 

    def get_player_ports(self, player_id):

        accessible = set()

        for port in self.ports:

            v1, v2 = port['vertices']

            if (

                (v1 in self.buildings and self.buildings[v1][0] == player_id) or

                (v2 in self.buildings and self.buildings[v2][0] == player_id)

            ):

                accessible.add(port['type'])

        return accessible

