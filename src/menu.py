import pyengine.pgwidgets as pgw
from pyengine.pgbasics import *
#
from .window import *
from . import fonts


def iter_widgets():
    return sum([l for l in widgets.values()], [])


pgw.set_hw_accel(False)

kwargs = {"anchor": "center", "template": "menu widget", "font": fonts.orbitron[15], "bg_color": (40, 40, 40, 210), "text_color": WHITE, "width": 168, "height": 32}
button_kwargs = {}
slider_kwargs = {"height": 66}

# the widget objects
widgets = {
    # "comboboxes": SmartList([
        # pgw.ComboBox(window.display, "Palette", ["asd", "dsa"], **kwargs),
    # ]),
    "checkboxes": SmartList([
        pgw.Checkbox(window.display, "Hitboxes", checked=False, **kwargs),
        pgw.Checkbox(window.display, "Collisions", checked=False, **kwargs),
        pgw.Checkbox(window.display, "Chunk Borders", checked=True, **kwargs),
        pgw.Checkbox(window.display, "Palettize", checked=False, **kwargs),
        pgw.Checkbox(window.display, "Lighting", checked=True, **kwargs),
        pgw.Checkbox(window.display, "Debug lighting", checked=False, **kwargs),
    ]),
    "sliders": SmartList([
        pgw.Slider(window.display, "FPS Cap", [10, 30, 60, 144, 165, float("inf")], 4, **kwargs | slider_kwargs),
    ]),
    "buttons": SmartList([
        pgw.Button(window.display, "Quit", lambda: None, pos=(300, 396), **kwargs | button_kwargs),
    ])
}

# binding variables to the widgets
hitboxes = widgets["checkboxes"].find(lambda x: x.text == "Hitboxes")
collisions = widgets["checkboxes"].find(lambda x: x.text == "Collisions")
chunk_borders = widgets["checkboxes"].find(lambda x: x.text == "Chunk Borders")
palettize = widgets["checkboxes"].find(lambda x: x.text == "Palettize")
lighting = widgets["checkboxes"].find(lambda x: x.text == "Lighting")
debug_lighting = widgets["checkboxes"].find(lambda x: x.text == "Debug lighting")
fps_cap = widgets["sliders"].find(lambda x: x.text == "FPS Cap")
quit = widgets["buttons"].find(lambda x: x.text == "Quit")

# organizing the widgets into neat grids
num_types = len(widgets.values())
if num_types % 2 == 1:
    render_range = range(-(num_types // 2), num_types // 2 + 1)
else:
    render_range = [-x for x in range(num_types // 2, 0, -1)] + [x for x in range(1, num_types // 2 + 1)]
for xo, widget_type in zip(render_range, widgets):
    xo *= kwargs["width"] + 4
    for yo, widget in enumerate(widgets[widget_type]):
        if widget_type == "sliders":
            margin = (kwargs["height"] + 2) * 2
        else:
            margin = kwargs["height"] + 2
        widget.set_pos((window.width / 2 + xo, 170 + yo * margin), "midtop")
