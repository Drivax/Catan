"""Run a standard benchmark comparison between baseline agents."""

from agents.random_agent import RandomAgent
from agents.smart_agent import SmartAgent
from charts import compare_agents


def main():
	agents_config = [
		SmartAgent(),
		SmartAgent(),
		RandomAgent(),
		RandomAgent(),
	]
	compare_agents(agents_config, num_games=300, max_turns=500)


if __name__ == "__main__":
	main()
