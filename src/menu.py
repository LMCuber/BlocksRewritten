import pyengine.pgwidgets as pgw
from pyengine.pgbasics import *
#
from .window import *
from . import fonts


kwargs = {"anchor": "center", "template": "menu widget", "font": fonts.orbitron[15], "bg_color": (40, 40, 40, 210), "text_color": WHITE}
target_fps = pgw.Slider(window.display, "Hor. Render Distance", [3, 30, 60, 120, 144, 165], -1, width=230, height=65, pos=(120, 100), **kwargs)
target_fps.enable()