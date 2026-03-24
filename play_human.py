"""Launch an interactive pygame visualization of a full game."""

from agents.smart_agent import SmartAgent
from game.core import CatanGame
import vizualize


def main():
	agents = [SmartAgent() for _ in range(4)]
	game = CatanGame(agents=agents, num_players=4, verbose=True)
	vizualize.draw_board(game, max_turns=150)


if __name__ == "__main__":
	main()
