import cProfile
import pstats
from pathlib import Path
import tomllib as toml
#
from src.game import Game


def run(config):
    game = Game(config=config)
    game.mainloop()


def profile(config):
    cProfile.run("run(config=config)", filename=Path("logs", "out.prof"))
    with open(Path("logs", "out.txt"), "w") as f:
        stats = pstats.Stats(str(Path("logs", "out.prof")), stream=f)
        stats.sort_stats("cumulative")
        stats.print_stats()


if __name__ == "__main__":
    with open(Path("config", "config.toml"), "rb") as f:
        config = toml.load(f)
    if config["game"]["profile"]:
        profile(config)
    else:
        run(config)