from agents.smart_agent import SmartAgent
from agents.random_agent import RandomAgent
from game.core import CatanGame
from charts import compare_agents
import vizualize

def main():
    """
    SmartAgent parameters:
    - prob_trade (float 0-1): Probability of wanting to trade each turn (default 0.7)
    - road_maker (0/1): If 1, prioritize road building (default 0)
    - greed (0/1): If 1, only accept favorable trades (1 for 2+) (default 0)
    
    Examples:
        SmartAgent() - Default: balanced trader, settlement-focused
        SmartAgent(prob_trade=0.9) - Wants to trade almost every turn
        SmartAgent(prob_trade=0.1) - Rarely trades
        SmartAgent(road_maker=1) - Prioritizes roads over settlements
        SmartAgent(greed=1) - Only accepts trades that give 2+ resources for 1
    """
    
    # Example 1: Default SmartAgent vs RandomAgent
    agents_config = [
        SmartAgent(),                               # Default balanced
        SmartAgent(prob_trade=0.9),                 # Aggressive trader
        SmartAgent(road_maker=1),                   # Road builder
        RandomAgent()
    ]
    compare_agents(agents_config, num_games=50, max_turns=500)
    
    # Example 2: Greedy agent comparison
    # agents_config = [
    #     SmartAgent(greed=0),
    #     SmartAgent(greed=1),
    #     SmartAgent(greed=1),
    #     RandomAgent()
    # ]
    # compare_agents(agents_config, num_games=50, max_turns=500)
    
    
    # Alternative: Regular game with visualization
    # agents = [SmartAgent() for _ in range(4)]
    # game = CatanGame(agents=agents, num_players=4)
    # vizualize.draw_board(game, max_turns=150)

if __name__ == "__main__":
    main()