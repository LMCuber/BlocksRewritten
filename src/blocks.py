from __future__ import annotations
import os
from collections import defaultdict
#
from pyengine.pgbasics import *
#
from .engine import *
from .window import *


# C O N S T A N T S
MAX_LIGHT = 12


# F U N C T I O N S
def darken(img, factor):
    darkened = img.copy()
    dark_overlay = pygame.Surface(img.size, pygame.SRCALPHA)
    alpha = factor * 255
    dark_overlay.fill((0, 0, 0, alpha))
    darkened.blit(dark_overlay, (0, 0))
    return darkened


def color_diff(c1, c2):
    return sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2)


def palettize_img(img, palette):
    ret_img = img.copy()
    palette_colors = [palette.get_at((x, 0)) for x in range(palette.width)]
    for y in range(img.height):
        for x in range(img.width):
            cur = img.get_at((x, y))
            closest: list[pygame.Color, int] = []
            for color in palette_colors:
                dist = color_diff(cur, color)
                if not closest or dist < closest[1]:
                    closest = [color, dist]
            ret_img.set_at((x, y), closest[0])
    return ret_img


"""
Block modifications:
    b - background block
"""
def norm(name: str) -> tuple[str, list[str]]:
    """
    Returns the normalized version of a block name, devoid of all modifiers e.g. stone|b (background stone) -> stone
    Normalized values are split by pipes.
    Quick check to know whether a fragmentation should be a norm or pure: if it has its own image and data, its a norm (e.g. tree_f has an image but tree_f|b does not)
    """
    spl = name.split("|")
    base: str = spl[0]
    mods: list[str] = spl[1:]
    return base, mods


def pure(name: str) -> tuple[str, list[str], str, list[str]]:
    """
    Returns the pure version, as well as the normalized version, of a block, which is its most important part. This is to make sure that for e.g. tree_f and tree_p don't get differentiated.
    Pure values are split by underscores.
    """
    base, mods = norm(name)
    spl = base.split("_")
    pure = spl[0]
    vers = spl[1:]
    return pure, spl, base, mods


def bwand(name: str, flag: BF):
    return get_data(name) & flag


def nbwand(name: str, flag: BF):
    return not (get_data(name) & flag)


def get_data(name):
    pur, spl, base, mods = pure(name)
    # default case (get from dictionary)
    return data[name]


# C L A S S E S
class _Suffix(str):
    def __ror__(self, other):
        base, mods = norm(other)
        if self in mods:
            return other
        return f"{base}|b"


class X:
    b = _Suffix("b")


class BF(IntFlag):
    """
    BF = BlockFlags
    """
    NONE = auto()
    WALKABLE = auto()
    BUILD = auto()
    CONSUME = auto()
    ORE = auto()
    ORGANIC = auto()
    UTIL = auto()
    GEAR = auto()
    NONSQUARE = auto()
    LIGHT_SOURCE = auto()
    EMPTY = auto()
    UNBREAKABLE = auto()


class OreData:
    def __init__(self):
        self.veins = {
            "base-ore": 4
        }


ores = OreData()

    
data = defaultdict(lambda: BF.NONE, {
    "sand": BF.ORGANIC,
    "dynamite": BF.UTIL,
    "lotus": BF.ORGANIC,
    "bed": BF.UTIL,
    "bed-right": BF.UTIL,
    "rock": BF.WALKABLE | BF.ORGANIC | BF.NONSQUARE,
    "rope": BF.WALKABLE,
    "karabiner": BF.WALKABLE,
    "workbench": BF.WALKABLE,
    "air": BF.EMPTY | BF.WALKABLE | BF.LIGHT_SOURCE | BF.UNBREAKABLE,
    "dirt_f" | X.b: BF.EMPTY | BF.LIGHT_SOURCE,
    "stone" | X.b: BF.EMPTY,
    "blackstone": BF.UNBREAKABLE,
    "torch": BF.LIGHT_SOURCE | BF.WALKABLE,
})

params = {
    "air": {"light": MAX_LIGHT},
    "torch": {"light": MAX_LIGHT, "light_falloff": 1},
    "dirt_f" | X.b: {"light": MAX_LIGHT}
}

# B L O C K  G R O U P S
pillars = [f"pillar_vr{i}" for i in range(4)]

# B L O C K  A S S E T S
d = Path("res", "images", "palettes")
palette_img = imgload("res", "images", "palettes", choice(os.listdir(d)))
palette_img = imgload("res", "images", "palettes", "2000.png")

block_list = [
    ["air",             "bucket",           "apple",           "bamboo",          "cactus",          "watermelon",       "rock",        "chicken",     "leaf_f",       "",            "",            ""],
    ["chest",           "snow",             "coconut",         "coconut-piece",   "command-block",   "wood",             "bed",         "bed-right",   "wood_f_vrLRT", "",            "",            ""],
    ["base-pipe",       "blast-furnace",    "dynamite",        "fire",            "magic-brick",     "watermelon-piece", "grass1",      "sand",        "wood_f_vrRT",  "",            "",            ""],
    ["hay",             "base-curved-pipe", "glass",           "grave",           "depr_leaf_f",     "workbench",        "grass2",      "sandstone",   "wood_f_vrLT",  "",            "",            ""],
    ["snow-stone",      "soil",             "stone",           "vine",            "wooden-planks",   "wooden-planks_a",  "stick",       "stone",       "wood_f_vrT",   "",            "",            ""],
    ["anvil",           "furnace",          "soil_p",          "bush",            "wooden-stairs",   "",                 "base-ore",    "bread",       "wood_f_vrLR",  "wood_sv_vrN", "wood_p_vrLR", ""],
    ["blackstone",      "closed-core",      "base-core",       "lava",            "base-orb",        "magic-table",      "base-armor",  "altar",       "wood_f_vrR",   "",            "wood_p_vrR",  ""],
    ["closed-door",     "wheat_st1",        "wheat_st2",       "wheat_st3",       "wheat_st4",       "stone-bricks",     "",            "arrow",       "wood_f_vrL",   "",            "wood_p_vrL",  ""],
    ["open-door",       "lotus",            "daivinus",        "dirt_f_depr",     "grass3",          "tool-crafter",     "bricks",      "solar-panel", "wood_f_vrN",   "",            "wood_p_vrN",  "wood_p"],
    ["cable_vrF",       "cable_vrH",        "karabiner",       "rope",            "blue_barrel",     "red_barrel",       "gun-crafter", "torch",       "grass_f",      "",            "",            "pillar_vr3"],
    ["",                "",                 "",                "corn-crop_vr3.2", "corn-crop_vr4.2", "",                 "",            "",            "soil_f",       "soil_t",      "",            "pillar_vr2"],
    ["",                "corn-crop_vr1.1",  "corn-crop_vr2.1", "corn-crop_vr3.1", "corn-crop_vr4.1", "cattail-top",      "pampas-top",  "",            "dirt_f",       "dirt_t",      "",            "pillar_vr1"],
    ["corn-crop_vr0.0", "corn-crop_vr1.0",  "corn-crop_vr2.0", "corn-crop_vr3.0", "corn-crop_vr4.0", "cattail",          "pampas",      "",            "",             "",            "",            "pillar_vr0"],
]
images = {}
_spritesheet = imgload("res", "images", "spritesheets", "blocks.png")

# load block images
for y, layer in enumerate(block_list):
    for x, name in enumerate(layer):
        images[name] = scale_by(_spritesheet.subsurface(x * BS / S, y * BS / S, BS / S, BS / S), S)

# additional dynamically generated blocks
images["coal"] = images["base-ore"]
images["iron"] = swap_palette(images["base-ore"], BLACK, (161, 157, 148))
images["diamond"] = swap_palette(images["base-ore"], BLACK, (185, 242, 255))

# create background blocks
for name, image in images.copy().items():
    images[name | X.b] = darken(images[name], 0.7)

# pygame.image.save(palettize_img(_spritesheet, palette_img), "pqweqwe.png")

breaking_sprs = imgload("res", "images", "visuals", "breaking.png", scale=S, frames=4)
inventory_img = imgload("res", "images", "visuals", "inventory.png", scale=S)
