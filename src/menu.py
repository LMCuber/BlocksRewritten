import pyengine.pgwidgets as pgw
from pyengine.pgbasics import *
#
from .window import *
from . import fonts


# pgw.set_hw_accel(False)

kwargs = {"anchor": "center", "template": "menu widget", "font": fonts.orbitron[15], "bg_color": (40, 40, 40, 210), "text_color": WHITE}
button_kwargs = {"width": 100}
# target_fps = pgw.Slider(window.display, "Hor. Render Distance", [3, 30, 60, 120, 144, 165, 240, 500], -1, width=230, height=65, pos=(120, 100), **kwargs)
# # target_fps.enable()

widgets = []
# widgets = SmartList([ 
#     pgw.Checkbox(window.display, "Hitboxes", pos=(300, 270), **kwargs),
#     pgw.Checkbox(window.display, "Chunk Borders", pos=(300, 300), **kwargs),
#     pgw.Button(window.display, "Quit", lambda: None, pos=(300, 330), **kwargs | button_kwargs),
# ])
# hitboxes = widgets.find(lambda x: x.text == "Hitboxes")
# chunk_borders = widgets.find(lambda x: x.text == "Chunk Borders")
# quit_button = widgets.find(lambda x: x.text == "Quit")
