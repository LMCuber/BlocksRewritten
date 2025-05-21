import cProfile
import pstats
#
from src.game import Game


def run():
    game = Game()
    game.mainloop()


def profile():
    cProfile.run("run()", filename="out.prof")
    with open("out.txt", "w") as f:
        stats = pstats.Stats("out.prof", stream=f)
        stats.sort_stats("cumulative")
        stats.print_stats()

if __name__ == "__main__":
    profile()
    # run()