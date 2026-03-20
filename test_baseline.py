"""Test baseline SmartAgent performance to verify it's better than random"""

import copy
from agents.smart_agent import SmartAgent
from agents.random_agent import RandomAgent
from game.core import CatanGame


def test_baseline_smartagent():
    """Test if default SmartAgent beats 3 RandomAgents"""
    print("Testing baseline SmartAgent performance...")
    print("=" * 60)
    
    # Create default SmartAgent vs RandomAgents
    smart_agent = SmartAgent()
    random_agents = [RandomAgent() for _ in range(3)]
    
    agents_template = [smart_agent] + random_agents
    
    wins = 0
    num_games = 100
    
    print(f"Playing {num_games} games: SmartAgent vs 3 RandomAgents")
    
    for game_num in range(num_games):
        agents = [copy.copy(agent) for agent in agents_template]
        game = CatanGame(agents=agents, num_players=4, verbose=False)
        winner = game.run_until_end(max_turns=500)
        
        if winner == 0:  # SmartAgent at position 0
            wins += 1
        
        if (game_num + 1) % 20 == 0:
            print(f"Progress: {game_num + 1}/{num_games} games, "
                  f"SmartAgent wins: {wins} ({wins/(game_num+1)*100:.1f}%)")
    
    winrate = wins / num_games
    print("=" * 60)
    print(f"RESULTS: SmartAgent won {wins}/{num_games} games ({winrate*100:.1f}%)")
    print(f"Expected baseline (random): ~25%")
    
    if winrate > 0.30:
        print("✓ SmartAgent significantly outperforms random agents")
    elif winrate > 0.25:
        print("~ SmartAgent slightly better than baseline")
    else:
        print("✗ SmartAgent NOT better than random - something is wrong")
    
    return winrate


if __name__ == "__main__":
    test_baseline_smartagent()
