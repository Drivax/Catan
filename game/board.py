# Tiles coordinates, intersections...

import random
from collections import Counter, defaultdict

HEX_RESOURCES_DISTRIB = (
    ["wood"]*4 + ["brick"]*3 + ["sheep"]*4 +
    ["wheat"]*4 + ["ore"]*3 + ["desert"]
)

# Créer une vraie grille hexagonale (axial ou cube coordinates)
# Lister les 54 intersections
# Lister les arêtes
# Vérifier les règles de placement (distance 2, connexion routes, etc.)

HEX_NUMBERS_DISTRIB = [2,3,3,4,4,5,5,6,6,8,8,9,9,10,10,11,11,12]

class HexTile:
    def __init__(self, resource, number=None):
        self.resource = resource
        self.number = number
        self.robber = resource == "desert"

class Board:
    def __init__(self):
        tiles = list(HEX_RESOURCES_DISTRIB)
        numbers = list(HEX_NUMBERS_DISTRIB)
        random.shuffle(tiles)
        random.shuffle(numbers)

        self.tiles = []
        num_idx = 0
        for res in tiles:
            number = None if res == "desert" else numbers[num_idx]
            if res != "desert":
                num_idx += 1
            self.tiles.append(HexTile(res, number))


        self.production_map = defaultdict(list)  # tiles = list of index

        for i, tile in enumerate(self.tiles):
            if tile.number:
                self.production_map[tile.number].append(i)

        self.robber_hex = next(i for i,t in enumerate(self.tiles) if t.robber)

    def produce(self, dice_value):
        produced = defaultdict(Counter)
        if dice_value == 7:
            return produced  

        for hex_idx in self.production_map[dice_value]:
            tile = self.tiles[hex_idx]
            if hex_idx == self.robber_hex:
                continue

            for player_id in range(4):
                produced[player_id][tile.resource] += 1  # TEMPORARY attriubution of one ressource per player per tile

        return produced