from collections import Counter
from game.rules import COST_ROAD, COST_SETTLEMENT, COST_CITY, VICTORY_POINTS_TO_WIN,POINTS_DIC

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

    def build_road(self, free_cost=False):
        if free_cost or self.can_build_road():
            if not free_cost:
                self.resources -= COST_ROAD
            self.roads_built += 1
            self.roads_left -= 1
            self.victory_points += POINTS_DIC["road"]
            return True
        return False
    
    def build_settlement(self,free_cost=False):
        if free_cost or self.can_build_settlement():
            if not free_cost:
                self.resources -= COST_SETTLEMENT
        self.settlements_built += 1
        self.settlements_left -= 1
        self.victory_points += POINTS_DIC["colony"]
        return True

    def build_city(self):
        if not self.can_build_city():
            return False
        self.resources -= COST_CITY
        self.cities_built += 1
        self.cities_left -= 1
        self.victory_points += POINTS_DIC["city"]
        return True

    def add_resources(self, counter):
        self.resources += counter

    def discard_half(self):
        total = sum(self.resources.values())
        if total <= 7:
            return Counter()
        
        discard = Counter()
        to_discard = total // 2 
        
        for res, amt in self.resources.items():
            if to_discard <= 0:
                break
            discard_amt = min(amt, to_discard)
            discard[res] += discard_amt
            self.resources[res] -= discard_amt
            to_discard -= discard_amt
        
        return discard
    
    def can_trade_to_bank(self,give_res,receive_res,port_types):
        if give_res==receive_res:
            return None
        count_give=self.resources[give_res]

        if give_res in port_types:
            ratio=2
        elif 'generic' in port_types:
            ratio=3
        else:
            ratio=4

        if count_give>=ratio:
            return ratio
        return None
    
    def execute_bank_trade(self, give_res, receive_res, ratio):
        if self.resources[give_res] < ratio:
            return False
        
        self.resources[give_res] -= ratio
        self.resources[receive_res] += 1
        return True
    
    def can_offer_trade(self, give_res, give_amount, receive_res, receive_amount):
        return self.resources[give_res] >= give_amount

    def execute_trade(self, give_res, give_amount, receive_res, receive_amount):
        if self.resources[give_res] < give_amount:
            return False
        self.resources[give_res] -= give_amount
        self.resources[receive_res] += receive_amount
        return True