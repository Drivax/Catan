"""Fine-tuning module for optimizing SmartAgent parameters using reinforcement learning"""

import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
import copy
import os
from datetime import datetime

from agents.smart_agent import SmartAgent
from agents.random_agent import RandomAgent
from game.core import CatanGame


class ParameterOptimizer:
    """Reinforcement learning agent for optimizing SmartAgent parameters"""
    
    def __init__(self, num_evaluations=50, games_per_eval=50):
        """
        Initialize the optimizer
        
        Args:
            num_evaluations: Number of parameter combinations to evaluate
            games_per_eval: Number of games to play per parameter combination
        """
        self.num_evaluations = num_evaluations
        self.games_per_eval = games_per_eval
        self.history = defaultdict(list)  # Track results over time
        self.best_params = None
        self.best_winrate = 0
        
        # Parameter search space - ranges for each parameter
        self.param_space = {
            'prob_trade': (0.3, 1.0),           # Probability of wanting to trade
            'road_maker': (0, 1),                # Binary: prioritize roads
            'greed': (0, 1),                     # Binary: only accept good trades
            'prob_weight': (0.5, 3.0),          # Probability vs diversity trade-off
            'diversity_weight': (0.5, 3.0),     # Resource diversity weight
            'trade_chaos': (0.0, 0.5),          # Probability of bad trades
            'sheep_hoarder': (0, 1),            # Binary: refuse to give sheep
            'dumb_thief': (0, 1),               # Binary: steal from leader
            'city_first': (0.0, 10.0),          # Bias toward upgrading settlements to cities
            'port_lover': (0, 1),               # Binary: prefer building near ports
        }
    
    def _generate_random_params(self):
        """Generate random parameters within search space"""
        params = {}
        for param_name, (min_val, max_val) in self.param_space.items():
            if param_name in ['road_maker', 'greed', 'sheep_hoarder', 'dumb_thief', 'port_lover']:
                # Binary parameters
                params[param_name] = bool(np.random.randint(0, 2))
            else:
                # Continuous parameters
                params[param_name] = np.random.uniform(min_val, max_val)
        return params
    
    def _mutate_params(self, params, mutation_rate=0.3):
        """Mutate parameters with smart adjustments"""
        mutated = copy.deepcopy(params)
        for param_name, (min_val, max_val) in self.param_space.items():
            if np.random.random() < mutation_rate:
                if param_name in ['road_maker', 'greed', 'sheep_hoarder', 'dumb_thief', 'port_lover']:
                    # Binary parameters: flip based on mutation strength
                    flip_prob = 0.5 + (mutation_rate * 0.2)
                    if np.random.random() < flip_prob:
                        mutated[param_name] = not mutated[param_name]
                else:
                    # Continuous parameters: smaller, smarter adjustments
                    current_val = mutated[param_name]
                    param_range = max_val - min_val
                    
                    # Scale noise by parameter range and mutation rate
                    sigma = param_range * 0.15 * mutation_rate
                    noise = np.random.normal(0, sigma)
                    
                    new_val = current_val + noise
                    mutated[param_name] = np.clip(new_val, min_val, max_val)
        
        return mutated
    
    def evaluate_params(self, params, evaluation_num=1):
        """
        Evaluate a parameter combination by playing games
        
        Args:
            params: Dictionary of parameters for SmartAgent
            evaluation_num: Current evaluation number (for reporting)
            
        Returns:
            win_rate: Win rate (0-1) for the SmartAgent player
        """
        test_agent = SmartAgent(**params)
        
        # Play against random agents
        agents_config = [
            test_agent,
            SmartAgent(),
            SmartAgent(),
            SmartAgent()
        ]
        
        wins = 0
        for game_num in range(self.games_per_eval):
            agents = [copy.copy(agent) for agent in agents_config]
            game = CatanGame(agents=agents, num_players=4, verbose=False)
            winner = game.run_until_end(max_turns=500)
            
            if winner == 0:  # Our SmartAgent is at position 0
                wins += 1
            
            if (game_num + 1) % max(1, self.games_per_eval // 5) == 0:
                print(f"  Eval {evaluation_num}: Game {game_num + 1}/{self.games_per_eval}", end='\r')
        
        win_rate = wins / self.games_per_eval
        return win_rate
    
    def optimize(self):
        """Run the parameter optimization loop with better exploration"""
        print(f"Starting parameter optimization: {self.num_evaluations} evaluations, "
              f"{self.games_per_eval} games per evaluation")
        print("=" * 80)
        
        # Start with GOOD initial parameters (defaults are better than random)
        current_params = {
            'prob_trade': 0.7,
            'road_maker': 0,
            'greed': 0,
            'prob_weight': 1.0,
            'diversity_weight': 1.0,
            'trade_chaos': 0.0,
            'sheep_hoarder': False,
            'dumb_thief': False,
            'city_first': 0.0,
            'port_lover': False
        }
        current_winrate = self.evaluate_params(current_params, evaluation_num=1)
        
        self.best_params = copy.deepcopy(current_params)
        self.best_winrate = current_winrate
        
        print(f"\nEvaluation 1/{self.num_evaluations}: Win rate = {current_winrate:.3f}")
        self._print_params(current_params)
        
        # Track evaluation history for better decision making
        eval_history = [(current_winrate, copy.deepcopy(current_params))]
        consecutive_rejections = 0
        
        # Main optimization loop - adaptive exploration
        for eval_num in range(2, self.num_evaluations + 1):
            # Adaptive mutation rate: increase if stuck, decrease if making progress
            base_mutation_rate = 0.3 + (consecutive_rejections * 0.1)
            base_mutation_rate = min(0.7, base_mutation_rate)  # Cap at 0.7
            
            # Generate candidate parameters through mutation
            candidate_params = self._mutate_params(current_params, mutation_rate=base_mutation_rate)
            candidate_winrate = self.evaluate_params(candidate_params, evaluation_num=eval_num)
            
            print(f"\nEvaluation {eval_num}/{self.num_evaluations}: Win rate = {candidate_winrate:.3f}")
            self._print_params(candidate_params)
            
            # Simulated annealing acceptance: accept worse solutions with decreasing probability
            temp = 1.0 - (eval_num / self.num_evaluations) * 0.9  # Cool down over time
            delta = candidate_winrate - current_winrate
            
            # Accept if better, or with probability based on temperature
            if delta > 0:
                accept = True
                print(f"  ✓ Accepted (improved +{delta:.3f})")
                consecutive_rejections = 0
            else:
                # Simulated annealing: accept worse solutions when hot, rarely when cold
                accept_prob = np.exp(delta / max(0.01, temp))
                accept = np.random.random() < accept_prob
                
                if accept:
                    print(f"  ✓ Accepted (worse by {delta:.3f}, SA probability {accept_prob:.2f})")
                    consecutive_rejections = 0
                else:
                    print(f"  ✗ Rejected (worse by {delta:.3f}, SA probability {accept_prob:.2f})")
                    consecutive_rejections += 1
            
            if accept:
                current_params = candidate_params
                current_winrate = candidate_winrate
            
            # Track best parameters found
            if current_winrate > self.best_winrate:
                self.best_winrate = current_winrate
                self.best_params = copy.deepcopy(current_params)
                print(f"  🌟 NEW BEST: {self.best_winrate:.3f}")
                consecutive_rejections = 0
            
            eval_history.append((current_winrate, copy.deepcopy(current_params)))
            
            # Store in history
            for param_name, value in current_params.items():
                param_key = param_name.replace('_', ' ').title()
                self.history[param_key].append([eval_num, value, current_winrate])
        
        print("\n" + "=" * 80)
        print(f"OPTIMIZATION COMPLETE")
        print(f"Best win rate found: {self.best_winrate:.3f} ({self.best_winrate*100:.1f}%)")
        print(f"Baseline (random agent vs 3 random): ~25%")
        print(f"Best parameters:")
        self._print_params(self.best_params)
        
        return self.best_params, self.best_winrate
    
    def _print_params(self, params):
        """Pretty print parameters"""
        for param_name, value in params.items():
            if isinstance(value, bool):
                print(f"    {param_name:20s} = {value}")
            else:
                print(f"    {param_name:20s} = {value:.3f}")
    
    def save_results(self, output_dir="fine_tuning_results"):
        """Save optimization results as graphs"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Plot parameter evolution
        num_params = len(self.history)
        num_cols = 3
        num_rows = (num_params + num_cols - 1) // num_cols
        
        fig, axes = plt.subplots(num_rows, num_cols, figsize=(16, 4 * num_rows))
        axes = axes.flatten() if num_params > 1 else [axes]
        
        for idx, (param_name, values_list) in enumerate(self.history.items()):
            values_array = np.array(values_list)
            evaluations = values_array[:, 0]
            param_values = values_array[:, 1]
            winrates = values_array[:, 2]
            
            ax = axes[idx]
            
            # Create secondary axis for win rate
            ax2 = ax.twinx()
            
            # Plot parameter value
            color1 = '#2E86AB'
            line1 = ax.plot(evaluations, param_values, 'o-', color=color1, linewidth=2, 
                           markersize=6, label=f'{param_name} value')
            ax.set_xlabel('Evaluation', fontsize=11, fontweight='bold')
            ax.set_ylabel(f'{param_name}', color=color1, fontsize=11, fontweight='bold')
            ax.tick_params(axis='y', labelcolor=color1)
            
            # Plot win rate
            color2 = '#A23B72'
            line2 = ax2.plot(evaluations, winrates, 's-', color=color2, linewidth=2, 
                            markersize=5, alpha=0.7, label='Win rate')
            ax2.set_ylabel('Win Rate', color=color2, fontsize=11, fontweight='bold')
            ax2.tick_params(axis='y', labelcolor=color2)
            ax2.set_ylim(0, 1)
            
            ax.set_title(f'{param_name} Evolution', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # Combined legend
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax.legend(lines, labels, loc='upper left', fontsize=9)
        
        # Hide unused subplots
        for idx in range(num_params, len(axes)):
            axes[idx].axis('off')
        
        plt.tight_layout()
        param_evolution_path = os.path.join(output_dir, f'parameter_evolution_{timestamp}.png')
        plt.savefig(param_evolution_path, dpi=150, bbox_inches='tight')
        print(f"\n[SAVED] Parameter evolution graph: {param_evolution_path}")
        plt.close()
        
        # Plot best parameters as bar chart
        fig, ax = plt.subplots(figsize=(12, 6))
        
        param_names = list(self.best_params.keys())
        param_values = []
        
        for name in param_names:
            val = self.best_params[name]
            # Normalize binary to 0/1 for visualization
            param_values.append(1.0 if val is True else (0.0 if val is False else val))
        
        colors = ['#FF6B6B' if isinstance(self.best_params[name], bool) else '#4ECDC4' 
                 for name in param_names]
        
        bars = ax.bar(range(len(param_names)), param_values, color=colors, 
                      alpha=0.8, edgecolor='black', linewidth=2)
        
        ax.set_ylabel('Parameter Value', fontsize=12, fontweight='bold')
        ax.set_title(f'Best Parameters Found (Win Rate: {self.best_winrate:.1%})', 
                    fontsize=14, fontweight='bold')
        ax.set_xticks(range(len(param_names)))
        ax.set_xticklabels([name.replace('_', '\n') for name in param_names], 
                           fontsize=10, fontweight='bold')
        ax.set_ylim(0, 3.5)
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for i, (bar, val) in enumerate(zip(bars, param_values)):
            height = bar.get_height()
            label = f"TRUE" if isinstance(self.best_params[param_names[i]], bool) and val == 1.0 else \
                   f"FALSE" if isinstance(self.best_params[param_names[i]], bool) and val == 0.0 else \
                   f"{val:.2f}"
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   label, ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#FF6B6B', edgecolor='black', label='Binary parameter'),
            Patch(facecolor='#4ECDC4', edgecolor='black', label='Continuous parameter')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=11)
        
        best_params_path = os.path.join(output_dir, f'best_parameters_{timestamp}.png')
        plt.savefig(best_params_path, dpi=150, bbox_inches='tight')
        print(f"[SAVED] Best parameters graph: {best_params_path}")
        plt.close()
        
        # Save best parameters to text file
        params_file = os.path.join(output_dir, f'best_parameters_{timestamp}.txt')
        with open(params_file, 'w') as f:
            f.write(f"SmartAgent Fine-Tuning Results\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"=" * 60 + "\n\n")
            f.write(f"Best Win Rate: {self.best_winrate:.1%}\n")
            f.write(f"Total Evaluations: {self.num_evaluations}\n")
            f.write(f"Games per Evaluation: {self.games_per_eval}\n")
            f.write(f"Total Games Played: {self.num_evaluations * self.games_per_eval}\n\n")
            f.write(f"Best Parameters:\n")
            f.write(f"-" * 60 + "\n")
            for param_name, value in self.best_params.items():
                f.write(f"{param_name:20s} = {value}\n")
            f.write(f"\n\nUsage in code:\n")
            f.write(f"best_agent = SmartAgent(\n")
            for param_name, value in self.best_params.items():
                f.write(f"    {param_name}={repr(value)},\n")
            f.write(f")\n")
        
        print(f"[SAVED] Parameters summary: {params_file}")
        
        return output_dir


def fine_tune(num_evaluations=50, games_per_eval=100):
    """
    Main fine-tuning function: reinforcement learning optimization of SmartAgent parameters
    
    This function uses simulated annealing to find SmartAgent parameters that maximize 
    win rate against random agents over multiple games.
    
    Algorithm:
    - Starts with GOOD defaults (not random)
    - Uses simulated annealing for exploration/exploitation balance
    - Adaptive mutation rate: increases when stuck, decreases when making progress
    - Temperature cools down over time (less likely to accept worse solutions)
    
    Args:
        num_evaluations: Number of parameter combinations to evaluate (default 50)
        games_per_eval: Number of games to play per parameter combination (default 100)
        
    Returns:
        Tuple of (best_params dict, best_winrate float)
        
    Example:
        best_params, winrate = fine_tune(num_evaluations=50, games_per_eval=100)
        best_agent = SmartAgent(**best_params)
    """
    print("\n" + "=" * 80)
    print("SMARTAGENT PARAMETER FINE-TUNING SYSTEM")
    print("=" * 80)
    
    optimizer = ParameterOptimizer(num_evaluations=num_evaluations, 
                                   games_per_eval=games_per_eval)
    best_params, best_winrate = optimizer.optimize()
    
    # Save visualizations
    output_dir = optimizer.save_results()
    
    print(f"\n✓ Fine-tuning complete! Results saved to '{output_dir}/'")
    print(f"✓ Best SmartAgent configuration ready to use\n")
    
    return best_params, best_winrate


if __name__ == "__main__":
    # Run fine-tuning with custom parameters
    best_params, best_winrate = fine_tune(num_evaluations=50, games_per_eval=500)
    
    # Create the optimized agent
    optimized_agent = SmartAgent(**best_params)
    print(f"\nOptimized SmartAgent created with win rate: {best_winrate:.1%}")
