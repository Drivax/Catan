"""Diagnostic test for fine-tuned SmartAgent performance"""

import copy
import numpy as np
from agents.smart_agent import SmartAgent
from agents.random_agent import RandomAgent
from game.core import CatanGame


def test_agent_vs_opponents(test_agent, opponent_type='smart_default', num_games=100):
    """Test an agent against different opponent types"""
    
    print(f"\nTesting vs {opponent_type.upper()}")
    print("=" * 60)
    
    if opponent_type == 'smart_default':
        opponents = [SmartAgent() for _ in range(3)]
        desc = "Default SmartAgents"
    elif opponent_type == 'random':
        opponents = [RandomAgent() for _ in range(3)]
        desc = "RandomAgents"
    elif opponent_type == 'smart_random':
        opponents = [
            SmartAgent(
                prob_trade=np.random.uniform(0.3, 1.0),
                road_maker=bool(np.random.randint(0, 2)),
                greed=bool(np.random.randint(0, 2)),
                prob_weight=np.random.uniform(0.5, 3.0),
                diversity_weight=np.random.uniform(0.5, 3.0),
                trade_chaos=np.random.uniform(0.0, 0.5),
                sheep_hoarder=bool(np.random.randint(0, 2)),
                dumb_thief=bool(np.random.randint(0, 2)),
                city_first=np.random.uniform(0.0, 10.0),
                port_lover=bool(np.random.randint(0, 2))
            )
            for _ in range(3)
        ]
        desc = "Randomized SmartAgents"
    
    wins = 0
    for game_num in range(num_games):
        agents = [copy.copy(test_agent)] + [copy.copy(opp) for opp in opponents]
        
        game = CatanGame(agents=agents, num_players=4, verbose=False)
        winner = game.run_until_end(max_turns=500)
        
        if winner == 0:
            wins += 1
        
        if (game_num + 1) % max(1, num_games // 5) == 0:
            print(f"Progress: {game_num + 1}/{num_games} games", end='\r')
    
    winrate = wins / num_games
    print(f"\nResults vs {desc}: {wins}/{num_games} wins = {winrate*100:.1f}%")
    print(f"Expected random in 4-player game: 25%")
    
    if winrate > 0.30:
        print("✓ Significantly BETTER than random")
    elif winrate > 0.25:
        print("~ Slightly better than random")
    elif winrate < 0.25:
        print("✗ WORSE than random!")
    else:
        print("= About the same as random")
    
    return winrate


def main():
    print("SMARTAGENT PERFORMANCE DIAGNOSTIC")
    print("=" * 60)
    
    # Default SmartAgent baseline
    default_agent = SmartAgent()
    
    # Fine-tuned agent from main.py
    tuned_agent = SmartAgent(
        prob_trade=0.7,
        road_maker=False,
        greed=0,
        prob_weight=1.0,
        diversity_weight=1.0,
        trade_chaos=0.0,
        sheep_hoarder=False,
        dumb_thief=True,  # Only real difference
        city_first=0.0,
        port_lover=False,
    )
    
    print("\n1. TESTING DEFAULT SMARTAGENT")
    default_vs_default = test_agent_vs_opponents(default_agent, 'smart_default', num_games=100)
    
    print("\n2. TESTING FINE-TUNED SMARTAGENT vs DEFAULT SMARTAGENTS")
    tuned_vs_default = test_agent_vs_opponents(tuned_agent, 'smart_default', num_games=100)
    
    print("\n3. TESTING FINE-TUNED SMARTAGENT vs RANDOM AGENTS")
    tuned_vs_random = test_agent_vs_opponents(tuned_agent, 'random', num_games=100)
    
    print("\n4. TESTING FINE-TUNED SMARTAGENT vs RANDOMIZED SMARTAGENTS")
    tuned_vs_random_smart = test_agent_vs_opponents(tuned_agent, 'smart_random', num_games=100)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Default SmartAgent vs Default SmartAgents: {default_vs_default*100:.1f}%")
    print(f"Fine-tuned SmartAgent vs Default SmartAgents: {tuned_vs_default*100:.1f}%")
    print(f"Fine-tuned SmartAgent vs Random Agents: {tuned_vs_random*100:.1f}%")
    print(f"Fine-tuned SmartAgent vs Randomized SmartAgents: {tuned_vs_random_smart*100:.1f}%")
    
    improvement = tuned_vs_default - default_vs_default
    print(f"\nImprovement over default: {improvement:+.1f}% ({improvement*100:+.0f} percentage points)")
    
    if improvement > 0:
        print("✓ Fine-tuning helped!")
    elif improvement < -2:
        print("✗ Fine-tuning made it WORSE!")
    else:
        print("~ Fine-tuning had negligible effect")


if __name__ == "__main__":
    main()
