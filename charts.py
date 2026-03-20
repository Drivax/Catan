"""Agent performance comparison and visualization module"""

import matplotlib.pyplot as plt
import copy
from game.core import CatanGame


def compare_agents(agent_template, num_games=100, max_turns=500):
    """Compare agents over multiple games
    
    Args:
        agent_template: List of 4 agent instances as template 
                       (e.g., [SmartAgent(), SmartAgent(), RandomAgent(), RandomAgent()])
        num_games: Number of games to play
        max_turns: Max turns per game
    """
    
    if len(agent_template) != 4:
        raise ValueError("agent_template must contain exactly 4 agents")
    
    # Create descriptive labels and parameter legends for each agent
    agent_labels = []
    agent_legends = []
    for i, agent in enumerate(agent_template):
        label = _get_agent_label(agent)
        agent_labels.append(label)
        # Collect all parameters for legend
        params = []
        if hasattr(agent, 'prob_trade'):
            params.append(f"prob_trade={agent.prob_trade}")
        if hasattr(agent, 'road_maker'):
            params.append(f"road_maker={agent.road_maker}")
        if hasattr(agent, 'greed'):
            params.append(f"greed={agent.greed}")
        if hasattr(agent, 'prob_weight'):
            params.append(f"prob_weight={agent.prob_weight}")
        if hasattr(agent, 'diversity_weight'):
            params.append(f"diversity_weight={agent.diversity_weight}")
        if hasattr(agent, 'trade_chaos'):
            params.append(f"trade_chaos={agent.trade_chaos}")
        if hasattr(agent, 'sheep_hoarder'):
            params.append(f"sheep_hoarder={agent.sheep_hoarder}")
        if hasattr(agent, 'dumb_thief'):
            params.append(f"dumb_thief={agent.dumb_thief}")
        legend = f"Player {i}: " + ", ".join(params)
        agent_legends.append(legend)
    
    # Count wins per agent (by position)
    agent_wins = {i: 0 for i in range(4)}
    
    print(f"Configuration:")
    for i, label in enumerate(agent_labels):
        print(f"  Player {i}: {label}")
    print(f"Simulating {num_games} games...")
    print("=" * 60)
    
    for game_num in range(num_games):
        # Create copies of template agents with same parameters
        agents = [copy.copy(template_agent) for template_agent in agent_template]
        
        game = CatanGame(agents=agents, num_players=4, verbose=False)
        winner = game.run_until_end(max_turns=max_turns)
        
        if winner is not None:
            agent_wins[winner] += 1
        
        if (game_num + 1) % max(1, num_games // 10) == 0:
            print(f"Progress: {game_num + 1}/{num_games} games")
            for i in range(4):
                pct = (agent_wins[i] / (game_num + 1) * 100) if game_num > 0 else 0
                print(f"  {agent_labels[i]:30s}: {agent_wins[i]:3d} wins ({pct:5.1f}%)")
    
    print("=" * 60)
    print(f"\nFinal Results ({num_games} games):")
    for i in range(4):
        pct = (agent_wins[i] / num_games * 100) if num_games > 0 else 0
        print(f"  Player {i}: {agent_labels[i]:30s} -> {agent_wins[i]:3d} wins ({pct:5.1f}%)")
    
    # Create visualizations
    create_charts(agent_wins, agent_labels, agent_legends, num_games)


def _get_agent_label(agent):
    """Generate a descriptive label for an agent including its parameters"""
    agent_type = agent.__class__.__name__
    
    # Check for SmartAgent-specific parameters
    if hasattr(agent, 'prob_trade') and hasattr(agent, 'road_maker') and hasattr(agent, 'greed'):
        params = []
        if agent.prob_trade != 0.7:
            params.append(f"trade={agent.prob_trade}")
        if agent.road_maker == 1:
            params.append("roads=1")
        if agent.greed == 1:
            params.append("greedy")
        
        if params:
            return f"{agent_type}({', '.join(params)})"
    
    return agent_type


def create_charts(agent_wins, agent_labels, agent_legends, num_games):
    """Create bar and pie charts for agent performance
    
    Args:
        agent_wins: Dict like {0: 25, 1: 20, 2: 30, 3: 25} (wins per player index)
        agent_labels: List of 4 descriptive labels for each agent
        agent_legends: List of 4 legend strings with all agent parameters
        num_games: Total number of games played
    """
    
    # Prepare data
    wins = [agent_wins[i] for i in range(4)]
    
    # Shortened labels for chart readability
    chart_labels = [f"P{i}: {label}" for i, label in enumerate(agent_labels)]
    
    # Color palette
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle(f'Agent Performance Comparison ({num_games} games)', 
                 fontsize=16, fontweight='bold')
    
    # Bar chart
    ax1 = axes[0]
    bars = ax1.bar(range(4), wins, color=colors, alpha=0.8, edgecolor='black', linewidth=2)
    ax1.set_ylabel('Number of Wins', fontsize=12, fontweight='bold')
    ax1.set_title('Total Wins per Agent', fontsize=13, fontweight='bold')
    ax1.set_xlabel('Player', fontsize=12, fontweight='bold')
    ax1.set_xticks(range(4))
    ax1.set_xticklabels(agent_labels, fontsize=10)
    max_wins = max(wins) if wins else 1
    ax1.set_ylim(0, max_wins * 1.15)
    ax1.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for i, (bar, win) in enumerate(zip(bars, wins)):
        height = bar.get_height()
        pct = (win / num_games * 100) if num_games > 0 else 0
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(win)}\n({pct:.1f}%)',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    # Add legend with agent parameters
    legend_text = '\n'.join(agent_legends)
    ax1.legend([legend_text], loc='lower right', fontsize=10, frameon=True)

    # Pie chart
    ax2 = axes[1]
    explode = [0.05] * 4
    ax2.pie(wins, labels=agent_labels, autopct='%1.1f%%', colors=colors,
            startangle=90, explode=explode, textprops={'fontsize': 10, 'fontweight': 'bold'})
    ax2.set_title('Win Rate Distribution', fontsize=13, fontweight='bold')

    plt.tight_layout()
    plt.savefig('agent_comparison.png', dpi=150, bbox_inches='tight')
    print("\n[SUCCESS] Chart saved as 'agent_comparison.png' with agent parameter legend")
    plt.show()
