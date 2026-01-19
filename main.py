from game.core import CatanGame
from agents.random_agent import RandomAgent
import random
import vizualize

def main():
    agents = [RandomAgent() for _ in range(4)]
    # random.seed(52)

    game=CatanGame(agents=agents,num_players=4)
    
    vizualize.draw_board(game)

    winner = game.run_until_end(max_turns=50)

if __name__ == "__main__":
    main()


    