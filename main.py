from game.core import CatanGame
from agents.random_agent import RandomAgent
import random


def main():
    agents = [RandomAgent() for _ in range(4)]
    # random.seed(52)

    game=CatanGame(agents=agents,num_players=4)
    winner = game.run_until_end(max_turns=5)

if __name__ == "__main__":
    main()
    