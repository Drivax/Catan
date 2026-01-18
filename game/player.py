from collections import Counter
from game.rules import COST_ROAD, COST_SETTLEMENT, COST_CITY, VICTORY_POINTS_TO_WIN

class Player:
    def __init__(self, pid):
        self.pid = pid
        self.resources = Counter()
        self.victory_points = 0
        self.roads_built = 0
        self.settlements_built = 0
        self.cities_built = 0

        self.settlements_left = 5
        self.cities_left = 4
        self.roads_left = 15

    def can_build_road(self):
        return self.roads_left > 0 and self.resources >= COST_ROAD

    def can_build_settlement(self):
        return self.settlements_left > 0 and self.resources >= COST_SETTLEMENT

    def can_build_city(self):
        return self.cities_left > 0 and self.resources >= COST_CITY

    def build_road(self):
        if not self.can_build_road():
            return False
        self.resources -= COST_ROAD
        self.roads_built += 1
        self.roads_left -= 1
        return True

    def build_settlement(self):
        if not self.can_build_settlement():
            return False
        self.resources -= COST_SETTLEMENT
        self.settlements_built += 1
        self.settlements_left -= 1
        self.victory_points += 1
        return True

    def build_city(self):
        if not self.can_build_city():
            return False
        self.resources -= COST_CITY
        self.cities_built += 1
        self.cities_left -= 1
        self.victory_points += 1  # +1
        return True

    def add_resources(self, counter):
        self.resources += counter