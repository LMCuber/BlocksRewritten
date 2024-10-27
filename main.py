from pathlib import Path
import pygame
import tomllib as toml
#
from pyengine.pgshaders import *
from pyengine.pgbasics import *
import pyengine.pgwidgets as pgw
#
from src.game import *
from src.entities import *
from src import fonts


class App:
    def __init__(self):
        self.game = Game(vsync=True)
        self.game.mainloop()
        self.game.quit()


app = App()
app.run()