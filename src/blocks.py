import os
#
from .engine import *
from .window import *



d = Path("res", "images", "palettes")
palette_img = imgload(Path("res", "images", "palettes", choice(os.listdir(d))), convert_alpha=False)
palette_img = imgload(Path("res", "images", "palettes", "dusted_sunset.png"), convert_alpha=False)


block_list = [
    ["air",             "bucket",           "apple",           "bamboo",          "cactus",          "watermelon",       "rock",        "chicken",     "leaf_f",       "",            "",            ""],
    ["chest",           "snow",             "coconut",         "coconut-piece",   "command-block",   "wood",             "bed",         "bed-right",   "wood_f_vrLRT", "",            "",            ""],
    ["base-pipe",       "blast-furnace",    "dynamite",        "fire",            "magic-brick",     "watermelon-piece", "grass1",      "sand",        "wood_f_vrRT",  "",            "",            ""],
    ["hay",             "base-curved-pipe", "glass",           "grave",           "depr_leaf_f",     "workbench",        "grass2",      "sandstone",   "wood_f_vrLT",  "",            "",            ""],
    ["snow-stone",      "soil",             "stone",           "vine",            "wooden-planks",   "wooden-planks_a",  "stick",       "stone",       "wood_f_vrT",   "",            "",            ""],
    ["anvil",           "furnace",          "soil_p",          "bush",            "wooden-stairs",   "",                 "base-ore",    "bread",       "wood_f_vrLR",  "wood_sv_vrN", "wood_p_vrLR", ""],
    ["blackstone",      "closed-core",      "base-core",       "lava",            "base-orb",        "magic-table",      "base-armor",  "altar",       "wood_f_vrR",   "",            "wood_p_vrR",  ""],
    ["closed-door",     "wheat_st1",        "wheat_st2",       "wheat_st3",       "wheat_st4",       "stone-bricks",     "",            "arrow",       "wood_f_vrL",   "",            "wood_p_vrL",  ""],
    ["open-door",       "lotus",            "daivinus",        "dirt_f_depr",     "grass3",          "tool-crafter",     "bricks",      "solar-panel", "wood_f_vrN",   "",            "wood_p_vrN",  ""],
    ["cable_vrF",       "cable_vrH",        "",                "",                "blue_barrel",     "red_barrel",       "gun-crafter", "torch",       "grass_f",      "",            "",            "asd4"],
    ["",                "",                 "",                "corn-crop_vr3.2", "corn-crop_vr4.2", "",                 "",            "",            "soil_f",       "soil_t",      "",            "asd3"],
    ["",                "corn-crop_vr1.1",  "corn-crop_vr2.1", "corn-crop_vr3.1", "corn-crop_vr4.1", "cattail-top",      "pampas-top",  "",            "dirt_f",       "dirt_t",      "",            "asd2"],
    ["corn-crop_vr0.0", "corn-crop_vr1.0",  "corn-crop_vr2.0", "corn-crop_vr3.0", "corn-crop_vr4.0", "cattail",          "pampas",      "",            "",             "",            "",            "asd1"],
]
images = {}
_spritesheet = imgload(Path("res", "images", "spritesheets", "blocks.png"))
for y, layer in enumerate(block_list):
    for x, block in enumerate(layer):
        images[block] = scale_by(_spritesheet.subsurface(x * BS / S, y * BS / S, BS / S, BS / S), S)
        