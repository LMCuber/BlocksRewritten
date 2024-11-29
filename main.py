from pathlib import Path
import pygame
import tomllib as toml
import cProfile
#
from pyengine.pgshaders import *
from pyengine.pgbasics import *
import pyengine.pgwidgets as pgw
#
from src.game import *
from src.entities import *
from src import fonts


def run():
    game = Game()
    game.mainloop()


if __name__ == "__main__":
    # cProfile.run("run()", sort="cumtime")
    run()