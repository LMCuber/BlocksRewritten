import cProfile
import pstats
import tomllib as toml
from pathlib import Path
#
from src.game import Game


def run(config):
    game = Game(config=config)
    game.mainloop()


def profile(config):
    Path("logs").mkdir(exist_ok=True)

    if config["game"]["profile_to_file"]:
        cProfile.run("run(config=config)", filename=Path("logs", "out.prof"))
    else:
        cProfile.run("run(config=config)", sort="cumtime")

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