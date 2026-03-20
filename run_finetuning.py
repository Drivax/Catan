"""
FINE-TUNING GUIDE: How to properly optimize SmartAgent parameters

This script shows the correct workflow for fine-tuning SmartAgent parameters
to beat a realistic mix of opponents (RandomAgents + SmartAgents).
"""

from fine_tuning import fine_tune
from agents.smart_agent import SmartAgent
from charts import compare_agents

def main():
    print("=" * 80)
    print("SMARTAGENT FINE-TUNING WORKFLOW")
    print("=" * 80)
    
    print("\nSTEP 1: Run parameter optimization")
    print("-" * 80)
    print("Optimizing against a realistic mix of opponents:")
    print("  • 50% RandomAgents")
    print("  • 25% Default SmartAgents") 
    print("  • 25% Randomized SmartAgents")
    print()
    print("This ensures the optimized agent can beat diverse strategies,")
    print("not just one specific type of opponent.")
    print()
    
    # Run fine-tuning
    best_params, best_winrate = fine_tune(num_evaluations=60, games_per_eval=150)
    
    print("\n" + "=" * 80)
    print("STEP 2: Test the optimized agent")
    print("-" * 80)
    print(f"Best win rate found during optimization: {best_winrate*100:.1f}%")
    print(f"Expected baseline (random): 25%")
    print()
    
    # Create optimized and baseline agents
    optimized_agent = SmartAgent(**best_params)
    baseline_agent = SmartAgent()  # Default parameters
    
    # Compare optimized vs baseline vs other default SmartAgents
    print("Now comparing optimized agent vs others in real games...")
    print()
    
    agents_config = [
        optimized_agent,  # Player 0: Optimized
        baseline_agent,   # Player 1: Baseline default
        SmartAgent(),     # Player 2: Baseline default
        SmartAgent()      # Player 3: Baseline default
    ]
    
    compare_agents(agents_config, num_games=200, max_turns=500)


if __name__ == "__main__":
    main()
