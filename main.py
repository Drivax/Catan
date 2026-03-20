from agents.smart_agent import SmartAgent
from agents.random_agent import RandomAgent
from game.core import CatanGame
from charts import compare_agents
import vizualize

def main():
    """
    SmartAgent parameters:
    - prob_trade (float 0-1): Probability of wanting to trade each turn (default 0.7)
    - road_maker (0/1): If 1, prioritize road building + brick tiles for starting settlements (default 0)
    - greed (0/1): If 1, only accept favorable trades (1 for 2+) (default 0)
    - prob_weight (float): Weight for tile probability in starting placement (default 1.0)
    - diversity_weight (float): Weight for resource diversity in starting placement (default 1.0)
    - trade_chaos (float 0-1): Probability of offering/accepting bad trades (default 0.0)
    - sheep_hoarder (bool or float): If True/1.0, refuses to give sheep away (default False)
    - dumb_thief (bool): If True, always steals from leader instead of weakest (default False)
    - city_first (float 0-10): Very high bias toward upgrading settlements to cities ASAP (default 0.0)
      "The Mayor" — few settlements, tall cities (higher values = upgrade earlier)
    - port_lover (bool): If True, strongly prefers building near ports even at bad locations (default False)
    
    RandomAgent parameters:
    - trade_chaos (float 0-1): Probability of offering/accepting bad trades (default 0.0)
    - sheep_hoarder (bool or float): If True/1.0, refuses to give sheep away (default False)
    - dumb_thief (bool): If True, always steals from leader instead of weakest (default False)
    
    Examples:
        SmartAgent() - Default: balanced trader, settlement-focused
        SmartAgent(road_maker=1) - Prioritizes roads and brick tiles for starting
        SmartAgent(prob_weight=2.0, diversity_weight=1.0) - Favor probability over diversity
        SmartAgent(sheep_hoarder=True, dumb_thief=True) - Sheep hoarder with dumb robber
        SmartAgent(city_first=8.0) - "The Mayor" - upgrades to cities very early
        SmartAgent(port_lover=True) - Focuses on ports for trading advantage
        SmartAgent(city_first=5.0, port_lover=True) - Mayor who controls ports
        RandomAgent(trade_chaos=0.5) - Sometimes makes bad trades
        RandomAgent(sheep_hoarder=True) - Never gives away sheep
        RandomAgent(dumb_thief=True) - Always targets the leader
    """
    
    # Run fine-tuned SmartAgent comparison
    # To generate fine-tuned parameters, use: from fine_tuning import fine_tune
    # best_params, winrate = fine_tune(num_evaluations=60, games_per_eval=150)
    
    agents_config = [
        SmartAgent(),  # Use defaults for fair baseline comparison
        SmartAgent(),
        SmartAgent(), 
        SmartAgent() 
    ]
    compare_agents(agents_config, num_games=500, max_turns=500)
    
    
    # Alternative: Regular game with visualization
    # agents = [SmartAgent() for _ in range(4)]
    # game = CatanGame(agents=agents, num_players=4, verbose=True)
    # vizualize.draw_board(game, max_turns=150)

if __name__ == "__main__":
    main()