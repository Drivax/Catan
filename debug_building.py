"""
Debug script to analyze building bottlenecks in Catan
"""
from game.core import CatanGame
from agents.smart_agent import SmartAgent
from agents.random_agent import RandomAgent
from collections import Counter

# Run a game and collect data
agents = [SmartAgent() for _ in range(4)]
game = CatanGame(agents=agents, num_players=4)

print("\n" + "="*70)
print("BUILDING COSTS ANALYSIS")
print("="*70)
print(f"Road:       1 wood + 1 brick")
print(f"Settlement: 1 wood + 1 brick + 1 sheep + 1 wheat (needs 4 types!)")
print(f"City:       2 wheat + 3 ore (needs 5 ore total!)")

print("\n" + "="*70)
print("RESOURCE DISTRIBUTION ON BOARD")
print("="*70)
from game.board import HEX_RESOURCES_DISTRIB, HEX_NUMBERS_DISTRIB
resource_count = Counter(HEX_RESOURCES_DISTRIB)
for res, count in resource_count.items():
    print(f"  {res:8}: {count} hexes")

print("\nNumbers: " + str(HEX_NUMBERS_DISTRIB))
print(f"Probability per dice roll: 6,8 (28.6%), 5,9 (22.2%), 4,10 (13.9%), 3,11 (8.3%), 2,12 (2.8%)")

print("\n" + "="*70)
print("GAME START: Initial Resources")
print("="*70)
for i, p in enumerate(game.players):
    print(f"J{i}: {dict(p.resources)}")

# Simulate some turns
print("\n" + "="*70)
print("SIMULATING 20 TURNS...")
print("="*70)

for _ in range(20):
    game.play_one_turn()
    game.current_player = (game.current_player + 1) % 4

print("\n" + "="*70)
print("AFTER 20 TURNS: Resource accumulation")
print("="*70)
for i, p in enumerate(game.players):
    total = sum(p.resources.values())
    res_str = " | ".join(f"{r}: {v}" for r, v in sorted(p.resources.items()) if v > 0)
    print(f"J{i} ({p.victory_points:2d} pts, {total:2d} total): {res_str}")

print("\n" + "="*70)
print("CAN BUILD ANALYSIS")
print("="*70)
for i, p in enumerate(game.players):
    print(f"\nJ{i}:")
    print(f"  Can build road?       {p.can_build_road()} (have: {dict(p.resources)})")
    print(f"  Can build settlement? {p.can_build_settlement()} (needs: wood, brick, sheep, wheat)")
    print(f"  Can build city?       {p.can_build_city()} (needs: 2 wheat + 3 ore)")
    print(f"  Settlements left: {p.settlements_left}")
    print(f"  Cities left: {p.cities_left}")

print("\n" + "="*70)
print("KEY INSIGHTS")
print("="*70)
print("1. Settlement needs 4 DIFFERENT resources - high barrier")
print("2. Ore is scarce (only 3 hexes) - cities are hard to build")
print("3. Random initial placement can leave players on low-probability numbers")
print("4. With only ~2 production sites per player, turns needed to gather 4 resources:")
print("   - Avg time per hex to produce = 2-3 turns (for 6,8) to 10-20 turns (for 4,10)")
print("   - Need 4 different resources = multiply by 4 = 8-80+ turns for first settlement!")
