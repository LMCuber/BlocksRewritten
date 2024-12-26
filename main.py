import cProfile
#
from src.game import Game


def run():
    game = Game()
    game.mainloop()


if __name__ == "__main__":
    # cProfile.run("run()", sort="cumtime")
    run()