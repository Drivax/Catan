"""
Test script to show turn counts for multiple games
"""
import subprocess
import re

def extract_turn_count(output):
    """Extract the final turn number from game output"""
    lines = output.split('\n')
    last_turn = 0
    for line in lines:
        match = re.match(r'\[\s*(\d+)\] Player', line)
        if match:
            last_turn = int(match.group(1))
    
    # Check if there was a winner
    if 'VICTOIRE' in output:
        return last_turn, 'WIN'
    elif 'Limite de tours' in output:
        return last_turn, 'TIMEOUT'
    return last_turn, 'UNKNOWN'

print("=" * 60)
print("SMART AGENT PERFORMANCE TEST")
print(f"{'Game':<8} {'Turns':<10} {'Status':<15} {'Winner'}")
print("=" * 60)

results = []
for game_num in range(1, 11):
    result = subprocess.run(
        ["C:/Users/Alexandre/anaconda3/envs/catan/python.exe", "main.py"],
        capture_output=True,
        text=True,
        cwd="c:\\Users\\Alexandre\\Documents\\code\\Catan"
    )
    
    output = result.stdout + result.stderr
    turns, status = extract_turn_count(output)
    
    # Find winner
    winner_match = re.search(r'VICTOIRE joueur (\d+)', output)
    winner = f"J{winner_match.group(1)}" if winner_match else "None"
    
    print(f"{game_num:<8} {turns:<10} {status:<15} {winner}")
    results.append((turns, status))

print("=" * 60)
avg_turns = sum(t for t, s in results) / len(results)
wins = sum(1 for t, s in results if s == 'WIN')
timeouts = sum(1 for t, s in results if s == 'TIMEOUT')

print(f"Average turns: {avg_turns:.1f}")
print(f"Wins: {wins}/10")
print(f"Timeouts: {timeouts}/10")
print(f"✓ All games completed within 50 turns!" if timeouts == 0 else f"✗ {timeouts} games hit 50-turn limit")
