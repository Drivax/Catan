# Tiles coordinates, intersections...

import random
from collections import Counter, defaultdict
from game.map import HEX_POSITIONS, get_corners
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
        tiles_resources = ["wood"]*4 + ["brick"]*3 + ["sheep"]*4 + ["wheat"]*4 + ["ore"]*3 + ["desert"]
        numbers = [2,3,3,4,4,5,5,6,6,8,8,9,9,10,10,11,11,12]
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

    def place_settlement(self, pid, vkey):
        if vkey in self.buildings:
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