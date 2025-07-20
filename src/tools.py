import pygame
import sys
import opensimplex as osim
from scipy.spatial import ConvexHull
#
from pyengine.pgbasics import *
from pyengine.basics import *
from pygame.math import Vector3 as Vec3
#
from src.window import *
from src.engine import *
from src import blocks


# initializations
# osimplex.seed(7)

# color definitions
grays = [(x, x, x, 255) for x in range(1, 256)]
browns = [(int(x * 0.6), int(x * 0.4), int(x * 0.2), 255) for x in range(1, 256)]
reds = [(x, 0, 0, 255) for x in range(1, 256)]
greens = [(0, x, 0, 255) for x in range(1, 256)]
blues = [(0, 0, x, 255) for x in range(1, 256)]
yellows = [(x, x, 0, 255) for x in range(1, 256)]

# funcs
get_gray = lambda mu, sigma: grays[int(nordis(mu, sigma))]
get_brown = lambda mu, sigma: browns[int(nordis(mu, sigma))]
get_red = lambda mu, sigma: reds[int(nordis(mu, sigma))]
get_green = lambda mu, sigma: greens[int(nordis(mu, sigma))]
get_blue = lambda mu, sigma: blues[int(nordis(mu, sigma))]
get_aquamarine = lambda n: pygame.Color(f"aquamarine{n}")
get_yellow = lambda mu, sigma: yellows[int(nordis(mu, sigma))]

# constantized colors
shigane = pygame.Color("#93CEC3")  # soft
kawagane = pygame.Color("#009A76")  # medium
hagane = pygame.Color("#255035")  # hard (aka tamahagane)

# other constants
current_module = sys.modules[__name__]

# constants
katana_mult = 300
compos_mult = 106
# compos_yvel = 0.015
compos_yvel = 0
compos_speed = 0.05


# functions
def get_crystal(type_, color=None):
    with open(path("src", "shapes", f"{type_}.json"), "r") as f:
        crystal_data = json.load(f)
    bcc = Crystal(
        window.display,
        crystal_data["vertices"],
        crystal_data["point_colors"] if color is None else [color] * len(crystal_data["vertices"]),
        crystal_data["connections"],
        [],
        (window.width / 2, window.height / 2), 18, 3, 0, 0, 0, 0.015, 0.015, 0.015
    )
    return bcc


def get_cube(base_color):
    poly = Crystal(window.display, "bow.obj", [], [], [], (400, 400), 200, 1, 0, 0, 0, 0, 0, 0, normalize=True, normals=False)
    return poly


def get_obj(path, mult=240):
    return Crystal(window.display, path, [], [], [], (400, 400), mult, 1, 0, 0, 0, 0, 0, 0, normalize=True, normals=False)


def get_sickle():
    poly = Crystal(window.display, Path("res", "objects", "bow.obj"), [], [], [], (window.center[0], window.center[1]), 280, 1, 0, 0, 0, 0, 0, 0, normalize=True, normals=True, mtl_file=Path("res", "objects", "bow.mtl"))
    return poly


def get_sphere(base_color):
    num_lon = 8
    num_lat = 8
    mult = 120
    name = f"{num_lon}x{num_lat}.obj"
    if os.path.isfile(path("src", "shapes", "spheres", name)) and False:
        sphere = Crystal(window.display, path("src", "shapes", "spheres", name), [], [], [], (940, 300), mult, 1, 0.2, 0.2, 0.3, 0.01, 0.01, 0.01, normalize=False)
    else:
        # calculations
        vertices = []
        r = 1
        point_r = 1
        for j in range(num_lat + 1):  # the + 1 does the bottom tip
            lat = j / num_lat * pi
            for i in range(num_lon):  # the + 1 is omitted with the laahnjituudessè because well performance reasons less vertices -> less calculations per frame
                lon = i / num_lon * (2 * pi)
                z = r * sin(lat) * cos(lon)
                x = r * sin(lat) * sin(lon)
                y = -r * cos(lat)
                m = osim.noise3(x=x * 3, y=y * 3, z=z * 3) * 0.6 + 1
                vertex = Vec3(x, y, z) * m
                if vertex not in vertices:
                    vertices.append(vertex)

        # fills
        fills = []
        # tip (triangles)
        fills.extend([
            [[[rand(0, 255)] * 4, (0, 0, 0, 0)], [0, (n + 1) if n < num_lon else 1, n]]
            for n in range(1, num_lon + 1)
        ])
        # body (quads)
        for y in range(num_lat - 2):
            fills.extend([
                [[[rand(0, 255)] * 4, (0, 0, 0, 0)], [y * num_lon + n, *((y * num_lon + n + 1, y * num_lon + n + num_lon + 1) if n < num_lon else (y * num_lon + 1, y * num_lon + num_lon + 1)), y * num_lon + n + num_lon]]
                for n in range(1, num_lon + 1)
            ])
        # bottom tip (triangles)
        fills.extend([
            [[[rand(0, 255)] * 4, (0, 0, 0, 0)], [(num_lat - 2) * num_lon + n, ((num_lat - 2) * num_lon + n + 1) if n < num_lon else ((num_lat - 2) * num_lon + 1), (num_lat - 1) * num_lon + 1]]
            for n in range(1, num_lon + 1)
        ])
        fills = []
        for simplex in hull.simplices:
            fill = [[[rand(0, 255)] * 4, (0, 0, 0, 0)], simplex]
            fills.append(fill)
        # object creation
        sphere = Crystal(
            window.display,
            vertices, [

            ], [
                # lines
            ],
            fills,
            (window.width / 2, window.height / 2), mult, point_r, 0, 0, 0, 0, 0, 0,
            fill_as_connections=False,
            backface_culling=False,
        )
    # sphere.save_to_file(path("src", "shapes", "spheres", name))
    return sphere
    

def get_rock(base_color):
    num_lon = 8
    num_lat = 8
    mult = 70
    av = 0.004
    
    # generate vertices
    vertices = []
    for _ in range(2 ** 9):
        point_r = random.random()
        u1 = random.random()
        u2 = random.random()
        phi = acos(2 * u1 - 1) - pi / 2
        lamb = 2 * pi * u2
        x = point_r * cos(phi) * cos(lamb)
        y = point_r * cos(phi) * sin(lamb)
        z = point_r * sin(phi)    
        vertices.append((x, y, z))

    # generate the triangles with convex hull algorithm
    hull = ConvexHull(vertices)
    fills = []
    for simplex in hull.simplices:
        fill = [[rgb_mult((218, 165, 32) if chance(1 / 20) else (65, 65, 65), randf(0.8, 1.2)), BLACK], simplex]
        fills.append(fill)

    # object creation
    sphere = Crystal(
        window.display,
        vertices, [

        ], [
            # lines
        ],
        fills,
        (window.width / 2, window.height / 2), mult, 1, 0, 0, 0, av, av, av,
        fill_as_connections=False,
        backface_culling=False,
    )
    return sphere


def get_icosahedron(base_color):
    mult = 40
    w, l = 1, phi
    vertices = [
        # vertical
        Vec3(-w, -l, 0),
        Vec3(w, -l, 0),
        Vec3(w, l, 0),
        Vec3(-w, l, 0),
        # horizontal
        Vec3(-l, 0, -w),
        Vec3(l, 0, -w),
        Vec3(l, 0, w),
        Vec3(-l, 0, w),
        # interplanar
        Vec3(0, -w, -l),
        Vec3(0, -w, l),
        Vec3(0, w, l),
        Vec3(0, w, -l),
    ]
    # vertices = [[p + randf(-1.2, 1.2) for p in v] for v in vertices]
    icosahedron = Crystal(
        window.display,
        vertices, [

        ], [

        ],
        [
            [[grays[rand(30, 100)], WHITE], [1, 0, 8]],
            [[grays[rand(30, 100)], WHITE], [0, 1, 9]],
            [[grays[rand(30, 100)], WHITE], [0, 9, 7]],
            [[grays[rand(30, 100)], WHITE], [0, 7, 4]],
            [[grays[rand(30, 100)], WHITE], [0, 4, 8]],
            [[grays[rand(30, 100)], WHITE], [8, 4, 11]],
            [[grays[rand(30, 100)], WHITE], [8, 11, 5]],
            [[grays[rand(30, 100)], WHITE], [8, 5, 1]],
            [[grays[rand(30, 100)], WHITE], [1, 5, 6]],
            [[grays[rand(30, 100)], WHITE], [1, 6, 9]],
            [[grays[rand(30, 100)], WHITE], [9, 10, 7]],
            [[grays[rand(30, 100)], WHITE], [9, 6, 10]],
            [[grays[rand(30, 100)], WHITE], [7, 10, 3]],
            [[grays[rand(30, 100)], WHITE], [7, 3, 4]],
            [[grays[rand(30, 100)], WHITE], [4, 3, 11]],
            [[grays[rand(30, 100)], WHITE], [11, 3, 2]],
            [[grays[rand(30, 100)], WHITE], [10, 2, 3]],
            [[grays[rand(30, 100)], WHITE], [6, 2, 10]],
            [[grays[rand(30, 100)], WHITE], [6, 5, 2]],
            [[grays[rand(30, 100)], WHITE], [5, 11, 2]],
        ],
        (window.width / 2, window.height / 2), mult, 2, 0, 0, 0, 0, 0, 0, 0,
        fill_as_connections=False,
    )
    return icosahedron


def get_sword(base_color):
    mult = 140
    w, l, h = 0.12, 0.8, 0.03
    tl = 0.3
    gw, gl, gh = 0.24, 0.1, 0.1
    gxo = l
    uw, ul, uh = 0.05, 0.4, 0.05
    uxo = gxo
    base_color = (235, 235, 235, 255)
    outline_color = (20, 20, 20, 255)
    sword = Crystal(
        window.display, [
            # base
            [-w, -l - tl, h],
            [w, -l, h],
            [w, l, h],
            [-w, l, h],
            [-w, -l - tl, -h],
            [w, -l, -h],
            [w, l, -h],
            [-w, l, -h],

            # guard
            [-gw, gxo, gh],
            [gw, gxo, gh],
            [gw, gxo + gl, gh],
            [-gw, gxo + gl, gh],
            [-gw, gxo, -gh],
            [gw, gxo, -gh],
            [gw, gxo + gl, -gh],
            [-gw, gxo + gl, -gh],

            # grip
            [-uw, uxo, uh],
            [uw, uxo, uh],
            [uw, uxo + ul, uh],
            [-uw, uxo + ul, uh],
            [-uw, uxo, -uh],
            [uw, uxo, -uh],
            [uw, uxo + ul, -uh],
            [-uw, uxo + ul, -uh],

            # PASS
        ], [
            # point colors
        ], [
            # lines
        ], [
            # fills
            # base
            [[base_color, outline_color], [0, 1, 2, 3]],
            [[base_color, outline_color], [4, 5, 1, 0]],
            [[base_color, outline_color], [5, 4, 7, 6]],
            [[base_color, outline_color], [3, 2, 6, 7]],
            [[base_color, outline_color], [4, 0, 3, 7]],
            [[base_color, outline_color], [1, 5, 6, 2]],

            # guard
            [[browns[90], outline_color], [0 + 8, 1 + 8, 2 + 8, 3 + 8]],
            [[browns[80], outline_color], [4 + 8, 5 + 8, 1 + 8, 0 + 8]],
            [[browns[70], outline_color], [5 + 8, 4 + 8, 7 + 8, 6 + 8]],
            [[browns[110], outline_color], [3 + 8, 2 + 8, 6 + 8, 7 + 8]],
            [[browns[120], outline_color], [4 + 8, 0 + 8, 3 + 8, 7 + 8]],
            [[browns[100], outline_color], [1 + 8, 5 + 8, 6 + 8, 2 + 8]],

            # grip
            [[browns[150], outline_color], [0 + 16, 1 + 16, 2 + 16, 3 + 16]],
            [[browns[140], outline_color], [4 + 16, 5 + 16, 1 + 16, 0 + 16]],
            [[browns[160], outline_color], [5 + 16, 4 + 16, 7 + 16, 6 + 16]],
            [[browns[170], outline_color], [3 + 16, 2 + 16, 6 + 16, 7 + 16]],
            [[browns[130], outline_color], [4 + 16, 0 + 16, 3 + 16, 7 + 16]],
            [[browns[120], outline_color], [1 + 16, 5 + 16, 6 + 16, 2 + 16]],
        ],
        (window.width / 2, window.height / 2), mult, 2, 0, 0, 0, 0, 0, 0
    )
    return sword


def get_katana(base_color):
    mult = 140
    gw, gl, gh = 0.07, 0.5, 0.04
    num_p = 5
    pw = 0.1
    pl = 0.05
    ps = (gl - pl * num_p) / (num_p + 1)
    bw, bl, bh = gw, gl * 2, gh
    # pattern
    pattern = []
    for yo in range(num_p):
        tip = (yo + 1) * ps + yo * pl + bl
        pattern.extend([
            (0, tip, gh),
            (pw / 2, tip + 0.5 * pl, gh + 0.01),
            (0, tip + pl, bh),
            (-pw / 2, tip + 0.5 * pl, gh + 0.01),
        ])
    pattern_fills = [
        [[WHITE, WHITE], [0 + 8 + n * 4, 1 + 8 + n * 4, 2 + 8 + n * 4, 3 + 8 + n * 4]] for n in range(num_p)
    ]
    # rest
    base_color = (235, 235, 235, 255)
    outline_color = (20, 20, 20, 255)
    katana = Crystal(
        window.display, [
            # base
            [-gw, bl, gh],
            [gw, bl, gh],
            [gw, bl + gl, gh],
            [-gw, bl + gl, gh],
            [-gw, bl, -gh],
            [gw, bl, -gh],
            [gw, bl + gl, -gh],
            [-gw, bl + gl, -gh],
            *pattern,
            # blade
            [-bw, -bl, bh],
            [bw, -bl, bh],
            [bw, bl, bh],
            [-bw, bl, bh],
            [-bw, -bl, -bh],
            [bw, -bl, -bh],
            [bw, bl, -bh],
            [-bw, bl, -bh],
        ], [
            # point colors
        ], [
            # lines
        ], [
            # fills
            [[grays[30]], [0, 1, 2, 3]],
            [[grays[30]], [5, 4, 7, 6]],
            [[grays[30]], [3, 2, 6, 7]],
            [[grays[30]], [4, 0, 3, 7]],
            [[grays[30]], [1, 5, 6, 2]],
            *pattern_fills,
            [[grays[240]], [0 + 8 + len(pattern), 1 + 8 + len(pattern), 2 + 8 + len(pattern), 3 + 8 + len(pattern)]],
            [[grays[240]], [4 + 8 + len(pattern), 5 + 8 + len(pattern), 1 + 8 + len(pattern), 0 + 8 + len(pattern)]],
            [[grays[240]], [5 + 8 + len(pattern), 4 + 8 + len(pattern), 7 + 8 + len(pattern), 6 + 8 + len(pattern)]],
            [[grays[240]], [3 + 8 + len(pattern), 2 + 8 + len(pattern), 6 + 8 + len(pattern), 7 + 8 + len(pattern)]],
            [[grays[240]], [4 + 8 + len(pattern), 0 + 8 + len(pattern), 3 + 8 + len(pattern), 7 + 8 + len(pattern)]],
            [[grays[240]], [1 + 8 + len(pattern), 5 + 8 + len(pattern), 6 + 8 + len(pattern), 2 + 8 + len(pattern)]],
        ],
        (window.width / 2, window.height / 2), mult, 2, 0, 0, 0, 0, 0.015, 0,
        fill_as_connections=False,
    )
    """
    sxo, syo = -w, -l
    sw, sl, sh = w / 2, w / 2, h
    sword_atom_shapes = [
        [[0, 0, 1], [1, 0, 1], [0, 1, 1]],
        [[1, 0, 1], [2, 0, 1], [2, 1, 1]],
        [[1, 0, 1], [1, 2, 1], [0, 1, 1]],
        [[0, 1, 1], [2, 1, 1], [1, 2, 1]],
        [[0, 1, 1], [1, 2, 1], [0, 2, 1]],
        [[2, 1, 1], [2, 2, 1], [1, 2, 1]]
    ]
    """
    return katana


def get_axe(base_color):
    mult = 140
    w, l, h = 0.05, 0.8, 0.05
    hw, hh = 0.35, 0.4
    base_color = (235, 235, 235, 255)
    blade_color = (50, 50, 50, 255)
    outline_color = (255, 255, 255, 255)
    axe = Crystal(
        window.display, [
            # base
            [-w, -l, h],
            [w, -l, h],
            [w, l, h],
            [-w, l, h],
            [-w, -l, -h],
            [w, -l, -h],
            [w, l, -h],
            [-w, l, -h],  # 7

            # head-back
            [w, -l, h],  # 8
            [w + hw, -l + hh * 0.25, h],  # 9
            [w, -l + hh * 0.5, h],  # 10
            # head-front
            # down
            [-w, -l + hh * 0.4, h],  # 11
            [-w - hw * 0.4, -l + hh * 0.4, h],  # 12
            [-w - hw * 0.8, -l + hh, 0],  # 13
            [-w - hw, -l + hh * 0.4, 0],  # 14
            # up (both z-layers | middle)
            [-w - hw * 0.8, -l - hh * 0.2, 0],  # 15
            [-w - hw * 0.6, -l, h],  # 16
            [-w, -l, h],  # 17
            # (2x, z-variance)
            # head-back
            [w, -l, -h],  # 18
            [w + hw, -l + hh * 0.25, -h],  # 19
            [w, -l + hh * 0.5, -h],  # 20
            # head-front
            # down
            [-w, -l + hh * 0.4, -h],  # 21
            [-w - hw * 0.4, -l + hh * 0.4, -h],  # 22
            # up
            [-w - hw * 0.6, -l, -h],  # 23
            [-w, -l, -h],  # 24
        ], [
            # point colors
        ], [
            # connections
        ], [
            # fills
            # base
            [[get_brown(160, 20), outline_color], [0, 1, 2, 3]],
            [[get_brown(160, 20), outline_color], [4, 5, 1, 0]],
            [[get_brown(160, 20), outline_color], [4, 5, 6, 7]],
            [[get_brown(160, 20), outline_color], [7, 6, 2, 3]],
            [[get_brown(160, 20), outline_color], [4, 0, 3, 7]],
            [[get_brown(160, 20), outline_color], [1, 5, 6, 2]],

            # back
            [[blade_color, outline_color], [8, 9, 10]],
            [[blade_color, outline_color], [18, 19, 20]],
            [[blade_color, outline_color], [18, 19, 9, 8]],
            [[blade_color, outline_color], [10, 9, 19, 20]],

            # head
            # stems
            [[blade_color, outline_color], [23, 24, 17, 16]],
            [[blade_color, outline_color], [15, 16, 23]],
            [[blade_color, outline_color], [22, 21, 11, 12]],
            [[blade_color, outline_color], [13, 12, 22]],
            # faces
            # section vermillion
            [[blade_color, outline_color], [16, 17, 11, 12]],
            [[blade_color, outline_color], [23, 24, 21, 22]],
            # section cyan
            [[blade_color, outline_color], [14, 15, 16, 12]],
            [[blade_color, outline_color], [14, 15, 23, 22]],
            # section olive
            [[blade_color, outline_color], [14, 13, 12]],
            [[blade_color, outline_color], [14, 13, 22]],

        ],
        (window.width / 2, window.height / 2), mult, 2, 0, 0, 0, 0, 0.015,0,
    )
    return axe


def get_shovel(base_color):
    mult = 140
    w, l, h = 0.05, 0.8, 0.03
    bw, bl, bh = 0.15, 0.35, 0.03
    tl = 0.1
    base_color = (235, 235, 235, 255)
    outline_color = (255, 255, 255, 255)
    shovel = Crystal(
        window.display, [
            # base
            [-w, -l, h],
            [w, -l, h],
            [w, l, h],
            [-w, l, h],
            [-w, -l, -h],
            [w, -l, -h],
            [w, l, -h],
            [-w, l, -h],  # 7

            # blade
            [-bw, l, -bh],
            [bw, l, -bh],
            [bw, l + bl, -bh],
            [-bw, l + bl, -bh],  # 11

            # tip
            [0, l + bl + tl, -bh],
        ], [
            # point colors
        ], [
            # connections
        ], [
            # fills
            # base
            [[browns[100], outline_color], [0, 1, 2, 3]],
            [[browns[90], outline_color], [4, 5, 1, 0]],
            [[browns[70], outline_color], [4, 5, 6, 7]],
            [[browns[80], outline_color], [7, 6, 2, 3]],
            [[browns[110], outline_color], [4, 0, 3, 7]],
            [[browns[120], outline_color], [1, 5, 6, 2]],

            # blade
            [[grays[180], outline_color], [8, 9, 10, 11]],

            # tip
            [[grays[170], outline_color], [10, 11, 12]],
        ],
        (window.width / 2, window.height / 2), mult, 2, 0, 0, 0, 0, 0.015,0,
        backface_culling=False,
    )
    return shovel


def get_pickaxe(base_color):
    mult = 140
    w, l, h = 0.05, 0.8, 0.05
    hw, hh = 0.35, 0.4
    base_color = (235, 235, 235, 255)
    outline_color = (255, 255, 255, 255)
    pickaxe = Crystal(
        window.display, [
            # base
            [-w, -l, h],
            [w, -l, h],
            [w, l, h],
            [-w, l, h],
            [-w, -l, -h],
            [w, -l, -h],
            [w, l, -h],
            [-w, l, -h],

            # head-back
            [w, -l, h],
            [w + hw, -l + hh * 0.25, h],
            [w, -l + hh * 0.5, h],
        ], [
            # point colors
        ], [
            # connections
        ], [
            # fills
            # base
            [[base_color, outline_color], [0, 1, 2, 3]],
            [[base_color, outline_color], [4, 5, 1, 0]],
            [[base_color, outline_color], [4, 5, 6, 7]],
            [[base_color, outline_color], [7, 6, 2, 3]],
            [[base_color, outline_color], [4, 0, 3, 7]],
            [[base_color, outline_color], [1, 5, 6, 2]],

            # head
            [[base_color, outline_color], [8, 9, 10]],

            # connecting the head

        ],
        (window.width / 2, window.height / 2), mult, 2, 0, 0, 0, 0, 0.015,0,
    )
    return pickaxe


def get_kunai(base_color):
    mult = 270
    w, l, h = 0.1, 0.55, 0.05
    mw, ml, mh = .3 * w, .32 * l, .3 * h
    gl = 0.75 * l
    base_color = (235, 235, 235, 255)
    outline_color = (255, 255, 255, 255)
    kunai = Crystal(
        window.display, [
            # base
            [-w, 0, 0],
            [0, 0, h],
            [w, 0, 0],
            [0, 0, -h],
            # tip
            [0, -l, 0],
            # middle
            [-mw, ml, 0],
            [0, ml, mh],
            [mw, ml, 0],
            [0, ml, -mh],
            # bottom
            [-mw, ml + gl, 0],
            [0, ml + gl, mh],
            [mw, ml + gl, 0],
            [0, ml + gl, -mh],
        ], [
            # point colors
        ], [
            # connections
        ], [
            # body and tip
            [[grays[50], outline_color], [0, 4, 1]],
            [[grays[40], outline_color], [1, 4, 2]],
            [[grays[70], outline_color], [2, 4, 3]],
            [[grays[60], outline_color], [3, 4, 0]],
            # middle
            [[grays[70], outline_color], [5, 0, 1, 6]],
            [[grays[60], outline_color], [6, 1, 2, 7]],
            [[grays[50], outline_color], [7, 2, 3, 8]],
            [[grays[40], outline_color], [8, 3, 0, 5]],
            # grip
            [[browns[50], outline_color], [9, 5, 6, 10]],
            [[browns[40], outline_color], [10, 6, 7, 11]],
            [[browns[70], outline_color], [11, 7, 8, 12]],
            [[browns[60], outline_color], [12, 8, 5, 9]],
            [[browns[60], outline_color], [9, 10, 11, 12]],
        ],
        (window.width / 2, window.height / 2), mult, 2, 0, 0, 0, 0, 0.015, 0,
    )
    return kunai


def get_spear(base_color):
    mult = 230
    w, l, h = 0.1, 0.55, 0.05
    mw, ml, mh = .3 * w, .32 * l, .3 * h
    gl = 0.75 * l
    base_color = (235, 235, 235, 255)
    outline_color = (255, 255, 255, 255)
    spear = Crystal(
        window.display, [
            # base
            [-w, 0, 0],
            [0, 0, h],
            [w, 0, 0],
            [0, 0, -h],
            # tip
            [0, -l, 0],
            # middle
            [-mw, ml, 0],
            [0, ml, mh],
            [mw, ml, 0],
            [0, ml, -mh],
            # bottom
            [-mw, ml + gl, 0],
            [0, ml + gl, mh],
            [mw, ml + gl, 0],
            [0, ml + gl, -mh],
        ], [
            # point colors
        ], [
            # connections
        ], [
            # body and tip
            [[grays[50], outline_color], [0, 4, 1]],
            [[grays[40], outline_color], [1, 4, 2]],
            [[grays[70], outline_color], [2, 4, 3]],
            [[grays[60], outline_color], [3, 4, 0]],
            # middle
            [[grays[70], outline_color], [5, 0, 1, 6]],
            [[grays[60], outline_color], [6, 1, 2, 7]],
            [[grays[50], outline_color], [7, 2, 3, 8]],
            [[grays[40], outline_color], [8, 3, 0, 5]],
            # grip
            [[browns[50], outline_color], [9, 5, 6, 10]],
            [[browns[40], outline_color], [10, 6, 7, 11]],
            [[browns[70], outline_color], [11, 7, 8, 12]],
            [[browns[60], outline_color], [12, 8, 5, 9]],
            [[browns[60], outline_color], [9, 10, 11, 12]],
        ],
        (window.width / 2, window.height / 2), mult, 2, 0, 0, 0, 0, 0.015, 0,
    )
    return spear


def get_spear(base_color):
    mult = 230
    w, l, h = 0.1, 0.55, 0.05
    mw, ml, mh = .3 * w, .32 * l, .3 * h
    gl = 0.75 * l
    base_color = (235, 235, 235, 255)
    outline_color = (255, 255, 255, 255)
    spear = Crystal(
        window.display, [
            # base
            [-w, 0, 0],
            [0, 0, h],
            [w, 0, 0],
            [0, 0, -h],
            # tip
            [0, -l, 0],
            # middle
            [-mw, ml, 0],
            [0, ml, mh],
            [mw, ml, 0],
            [0, ml, -mh],
            # bottom
            [-mw, ml + gl, 0],
            [0, ml + gl, mh],
            [mw, ml + gl, 0],
            [0, ml + gl, -mh],
        ], [
            # point colors
        ], [
            # connections
        ], [
            # body and tip
            [[grays[50], outline_color], [0, 4, 1]],
            [[grays[40], outline_color], [1, 4, 2]],
            [[grays[70], outline_color], [2, 4, 3]],
            [[grays[60], outline_color], [3, 4, 0]],
            # middle
            [[grays[70], outline_color], [5, 0, 1, 6]],
            [[grays[60], outline_color], [6, 1, 2, 7]],
            [[grays[50], outline_color], [7, 2, 3, 8]],
            [[grays[40], outline_color], [8, 3, 0, 5]],
            # grip
            [[browns[50], outline_color], [9, 5, 6, 10]],
            [[browns[40], outline_color], [10, 6, 7, 11]],
            [[browns[70], outline_color], [11, 7, 8, 12]],
            [[browns[60], outline_color], [12, 8, 5, 9]],
        ],
        (window.width / 2, window.height / 2), mult, 2, 0, 0, 0, 0, 0.015, 0,
    )
    return spear


def get_bow(base_color):
    mult = 230
    # base
    bw, bl, bh = 0.02, 0.4, 0.02
    bo = -0.2
    # string
    sw, sl, sh = 0.007, 0.7, 0.007
    so = 0.2
    base_color = (235, 235, 235, 255)
    outline_color = (255, 255, 255, 255)
    bow = Crystal(
        window.display, [
            # base
            [bo + -bw, -bl, bh],
            [bo + bw, -bl, bh],
            [bo + bw, bl, bh],
            [bo + -bw, bl, bh],
            [bo + -bw, -bl, -bh],
            [bo + bw, -bl, -bh],
            [bo + bw, bl, -bh],
            [bo + -bw, bl, -bh],

            # string
            [so + -sw, -sl, sh],
            [so + sw, -sl, sh],
            [so + sw, sl, sh],
            [so + -sw, sl, sh],
            [so + -sw, -sl, -sh],
            [so + sw, -sl, -sh],
            [so + sw, sl, -sh],
            [so + -sw, sl, -sh],
        ], [
            # point colors
        ], [
            # connections
        ], [
            # body
            [[get_brown(120, 20), outline_color], [0, 1, 2, 3]],
            [[get_brown(120, 20), outline_color], [4, 5, 1, 0]],
            [[get_brown(120, 20), outline_color], [4, 5, 6, 7]],
            [[get_brown(120, 20), outline_color], [7, 6, 2, 3]],
            [[get_brown(120, 20), outline_color], [4, 0, 3, 7]],
            [[get_brown(120, 20), outline_color], [1, 5, 6, 2]],
            # string
            [[get_brown(160, 20), outline_color], [0 + 8, 1 + 8, 2 + 8, 3 + 8]],
            [[get_brown(160, 20), outline_color], [4 + 8, 5 + 8, 1 + 8, 0 + 8]],
            [[get_brown(160, 20), outline_color], [4 + 8, 5 + 8, 6 + 8, 7 + 8]],
            [[get_brown(160, 20), outline_color], [7 + 8, 6 + 8, 2 + 8, 3 + 8]],
            [[get_brown(160, 20), outline_color], [4 + 8, 0 + 8, 3 + 8, 7 + 8]],
            [[get_brown(160, 20), outline_color], [1 + 8, 5 + 8, 6 + 8, 2 + 8]],
            # connect-top
            [[get_brown(160, 20), outline_color], [1 + 8, 5 + 8, 6 + 8, 2 + 8]],
        ],
        (window.width / 2, window.height / 2), mult, 2, 0, 0, 0, 0, 0.015, 0,
    )
    return bow


def get_hammer(base_color):
    # hammer head
    mult = 140
    hwi, hli, hhi = 0.4, 0.20, 0.20
    o = 0.07
    hwo, hlo, hho = hwi + o, hli + o, hhi + o
    bw, bl, bh = 0.08, 0.8, 0.08
    # hammer base
    # rest (also importante)
    hammer = Crystal(
        window.display, [
            # front head
            (-hwi, -hli - bl, hho),
            (hwi, -hli - bl, hho),
            (hwi, hli - bl, hho),
            (-hwi, hli - bl, hho),
            # back head
            (-hwi, -hli - bl, -hho),
            (hwi, -hli - bl, -hho),
            (hwi, hli - bl, -hho),
            (-hwi, hli - bl, -hho),
            # top head
            (-hwi, -hlo - bl, -hhi),
            (hwi, -hlo - bl, -hhi),
            (hwi, -hlo - bl, hhi),
            (-hwi, -hlo - bl, hhi),
            # bottom head
            (-hwi, hlo - bl, hhi),
            (hwi, hlo - bl, hhi),
            (hwi, hlo - bl, -hhi),
            (-hwi, hlo - bl, -hhi),
            # left head
            (-hwo, -hli - bl, -hli),
            (-hwo, -hli - bl, hli),
            (-hwo, hli - bl, hli),
            (-hwo, hli - bl, -hli),
            # right head
            (hwo, -hli - bl, hli),
            (hwo, -hli - bl, -hli),
            (hwo, hli - bl, -hli),
            (hwo, hli - bl, hli),
            # base
            (-bw, hlo - bl, bh),
            (bw, hlo - bl, bh),
            (bw, bl, bh),
            (-bw, bl, bh),
            (-bw, hlo - bl, -bh),
            (bw, hlo - bl, -bh),
            (bw, bl, -bh),
            (-bw, bl, -bh),
        ], [

        ], [

        ], [
            # faces
            [[grays[180], None], [0, 1, 2, 3]],
            [[grays[180], None], [5, 4, 7, 6]],
            [[grays[180], None], [8, 9, 10, 11]],
            [[grays[180], None], [12, 13, 14, 15]],
            [[grays[180], None], [16, 17, 18, 19]],
            [[grays[180], None], [20, 21, 22, 23]],
            # top edges
            [[grays[110], None], [11, 10, 1, 0]],
            [[grays[110], None], [8, 11, 17, 16]],
            [[grays[110], None], [9, 8, 4, 5]],
            [[grays[110], None], [10, 9, 21, 20]],
            # middle edges
            [[grays[110], None], [1, 20, 23, 2]],
            [[grays[110], None], [21, 5, 6, 22]],
            [[grays[110], None], [4, 16, 19, 7]],
            [[grays[110], None], [17, 0, 3, 18]],
            # bottom edges
            [[grays[110], None], [3, 2, 13, 12]],
            [[grays[110], None], [23, 22, 14, 13]],
            [[grays[110], None], [6, 7, 15, 14]],
            [[grays[110], None], [19, 18, 12, 15]],
            # top corners
            [[grays[230], None], [1, 10, 20]],
            [[grays[230], None], [21, 9, 5]],
            [[grays[230], None], [4, 8, 16]],
            [[grays[230], None], [17, 11, 0]],
            # bottom corners
            [[grays[230], None], [13, 2, 23]],
            [[grays[230], None], [12, 18, 3]],
            [[grays[230], None], [14, 22, 6]],
            [[grays[230], None], [15, 7, 19]],
            # bases
            [[browns[100], None], [24 + 0, 24 + 1, 24 + 2, 24 + 3]],
            [[browns[110], None], [24 + 4, 24 + 5, 24 + 1, 24 + 0]],
            [[browns[90], None], [24 + 5, 24 + 4, 24 + 7, 24 + 6]],
            [[browns[80], None], [24 + 3, 24 + 2, 24 + 6, 24 + 7]],
            [[browns[120], None], [24 + 4, 24 + 0, 24 + 3, 24 + 7]],
            [[browns[130], None], [24 + 1, 24 + 5, 24 + 6, 24 + 2]],
        ],
        (window.width / 2, window.height / 2), mult, 2, 0, 0, 0, 0, 0.015, 0,
    )
    return hammer


def get_dart(base_color):
    get_color = choice((get_red, get_blue, get_green))
    get_acolor = lambda mu, sigma: list(get_color(mu, sigma)[:3]) + [150]
    mult = 140
    #
    dw, dl, dh = 0.05, 0.6, 0.06
    bw, bl, bh = dw * 1.2, dl * 1.4, dh * 1.3
    uw, ul, uh = bw * 0.3, bl * 0.1, bh * 0.3
    tl = bl * 1.1
    wuw, wul = dw * 3, dl * 0.5
    wdw, wdl = dw * 3, dl * 0.5
    #
    base_color = (235, 235, 235, 255)
    outline_color = None
    dart = Crystal(
        window.display, [
            # down
            [0, dl, 0],
            [-dw, 0, dh],
            [dw, 0, dh],
            [dw, 0, -dh],
            [-dw, 0, -dh],
            # base
            [-bw, -bl, bh],
            [bw, -bl, bh],
            [bw, -bl, -bh],
            [-bw, -bl, -bh],
            # up
            [-uw, -bl - ul, uh],
            [uw, -bl - ul, uh],
            [uw, -bl - ul, -uh],
            [-uw, -bl - ul, -uh],
            # tip
            [0, -bl - tl, 0],
            # wings
            # left
            [-wuw, dl + wul, 0],
            [-wdw, dl + wul + wdl, 0],
            [0, dl + wul + wdl, 0],
            # right
            [wdw, dl + wul + wdl, 0],
            [wuw, dl + wul, 0],
            # front
            [0, dl + wul, wuw],
            [0, dl + wul + wdl, wdw],
            # back
            [0, dl + wul, -wuw],
            [0, dl + wul + wdl, -wdw],
        ], [
            # point colors
        ], [
            # connections
        ], [
            # fills
            # down
            [[get_color(140, 20), outline_color], [0, 1, 2]],
            [[get_color(140, 20), outline_color], [0, 2, 3]],
            [[get_color(140, 20), outline_color], [0, 3, 4]],
            [[get_color(140, 20), outline_color], [0, 4, 1]],
            # base
            [[get_yellow(140, 20), outline_color], [5, 6, 2, 1]],
            [[get_yellow(140, 20), outline_color], [6, 7, 3, 2]],
            [[get_yellow(140, 20), outline_color], [7, 8, 4, 3]],
            [[get_yellow(140, 20), outline_color], [8, 5, 1, 4]],
            # up
            [[get_yellow(140, 20), outline_color], [9, 10, 6, 5]],
            [[get_yellow(140, 20), outline_color], [10, 11, 7, 6]],
            [[get_yellow(140, 20), outline_color], [11, 12, 8, 7]],
            [[get_yellow(140, 20), outline_color], [12, 9, 5, 8]],
            # tip
            [[get_gray(90, 20), outline_color], [13, 9, 10]],
            [[get_gray(90, 20), outline_color], [13, 10, 11]],
            [[get_gray(90, 20), outline_color], [13, 11, 12]],
            [[get_gray(90, 20), outline_color], [13, 12, 9]],
            # wings
            # left
            [[get_acolor(230, 20), outline_color], [0, 14, 15, 16]],
            # right
            [[get_acolor(230, 20), outline_color], [0, 16, 17, 18]],
            # front
            [[get_acolor(230, 20), outline_color], [19, 20, 16, 0]],
            # back
            [[get_acolor(230, 20), outline_color], [21, 22, 16, 0]],
        ],
        (window.width / 2, window.height / 2), mult, 2, 0, 0, 0, 0, 0.015, 0,
        backface_culling=False,
    )
    return dart


def get_staff(base_color):
    mult = 140
    w, l, h = 0.06, 1.2, 0.06
    ow, ol, oh = 0.15, 0.15, 0.15
    oo = 0
    base_color = (235, 235, 235, 255)
    blade_color = (50, 50, 50, 255)
    outline_color = (255, 255, 255, 255)
    hammer = Crystal(
        window.display, [
            # base
            [-w, -l, h],
            [w, -l, h],
            [w, l, h],
            [-w, l, h],
            [-w, -l, -h],
            [w, -l, -h],
            [w, l, -h],
            [-w, l, -h],
            # orb BL
            [-w, -l, h],
            [-w, -l - ol, h],
            [-w - ow, -l - ol, h],
            [-w - ow, -l, h],
            [-w, -l, h + oh],
            [-w, -l - ol, h + oh],
            [-w - ow, -l - ol, h + oh],
            [-w - ow, -l, h + oh],
            # orb BR
            [ow + w * 2 -w, -l, h],
            [ow + w * 2 -w, -l - ol, h],
            [ow + w * 2 -w - ow, -l - ol, h],
            [ow + w * 2 -w - ow, -l, h],
            [ow + w * 2 -w, -l, h + oh],
            [ow + w * 2 -w, -l - ol, h + oh],
            [ow + w * 2 -w - ow, -l - ol, h + oh],
            [ow + w * 2 -w - ow, -l, h + oh],
            # orb TR
            [ow + w * 2 -w, -l, h - oh - h * 2],
            [ow + w * 2 -w, -l - ol, h - oh - h * 2],
            [ow + w * 2 -w - ow, -l - ol, h - oh - h * 2],
            [ow + w * 2 -w - ow, -l, h - oh - h * 2],
            [ow + w * 2 -w, -l, h + oh - oh - h * 2],
            [ow + w * 2 -w, -l - ol, h + oh - oh - h * 2],
            [ow + w * 2 -w - ow, -l - ol, h + oh - oh - h * 2],
            [ow + w * 2 -w - ow, -l, h + oh - oh - h * 2],
            # orb TL
            [-w, -l, h - oh - h * 2],
            [-w, -l - ol, h - oh - h * 2],
            [-w - ow, -l - ol, h - oh - h * 2],
            [-w - ow, -l, h - oh - h * 2],
            [-w, -l, h + oh - oh - h * 2],
            [-w, -l - ol, h + oh - oh - h * 2],
            [-w - ow, -l - ol, h + oh - oh - h * 2],
            [-w - ow, -l, h + oh - oh - h * 2],
        ], [
            # point colors
        ], [
            # connections
        ], [
            # fills
            # base
            [[blocks.images["wooden-planks"], None], [0, 1, 2, 3]],
            [[blocks.images["wooden-planks"], None], [4, 5, 1, 0]],
            [[blocks.images["wooden-planks"], None], [5, 4, 7, 6]],
            [[blocks.images["wooden-planks"], None], [3, 2, 6, 7]],
            [[blocks.images["wooden-planks"], None], [4, 0, 3, 7]],
            [[blocks.images["wooden-planks"], None], [1, 5, 6, 2]],
            # orb BL
            [[get_aquamarine(choice(list(range(1, 4)) + [""])), outline_color], [0 + 8, 1 + 8, 2 + 8, 3 + 8]],
            [[get_aquamarine(choice(list(range(1, 4)) + [""])), outline_color], [4 + 8, 5 + 8, 1 + 8, 0 + 8]],
            [[get_aquamarine(choice(list(range(1, 4)) + [""])), outline_color], [5 + 8, 4 + 8, 7 + 8, 6 + 8]],
            [[get_aquamarine(choice(list(range(1, 4)) + [""])), outline_color], [3 + 8, 2 + 8, 6 + 8, 7 + 8]],
            [[get_aquamarine(choice(list(range(1, 4)) + [""])), outline_color], [4 + 8, 0 + 8, 3 + 8, 7 + 8]],
            [[get_aquamarine(choice(list(range(1, 4)) + [""])), outline_color], [1 + 8, 5 + 8, 6 + 8, 2 + 8]],
            # orb BR
            [[get_green(150, 20), outline_color], [0 + 8 * 2, 1 + 8 * 2, 2 + 8 * 2, 3 + 8 * 2]],
            [[get_green(150, 20), outline_color], [4 + 8 * 2, 5 + 8 * 2, 1 + 8 * 2, 0 + 8 * 2]],
            [[get_green(150, 20), outline_color], [5 + 8 * 2, 4 + 8 * 2, 7 + 8 * 2, 6 + 8 * 2]],
            [[get_green(150, 20), outline_color], [3 + 8 * 2, 2 + 8 * 2, 6 + 8 * 2, 7 + 8 * 2]],
            [[get_green(150, 20), outline_color], [4 + 8 * 2, 0 + 8 * 2, 3 + 8 * 2, 7 + 8 * 2]],
            [[get_green(150, 20), outline_color], [1 + 8 * 2, 5 + 8 * 2, 6 + 8 * 2, 2 + 8 * 2]],
            # orb TR
            [[get_gray(140, 20), outline_color], [0 + 8 * 3, 1 + 8 * 3, 2 + 8 * 3, 3 + 8 * 3]],
            [[get_gray(140, 20), outline_color], [4 + 8 * 3, 5 + 8 * 3, 1 + 8 * 3, 0 + 8 * 3]],
            [[get_gray(140, 20), outline_color], [5 + 8 * 3, 4 + 8 * 3, 7 + 8 * 3, 6 + 8 * 3]],
            [[get_gray(140, 20), outline_color], [3 + 8 * 3, 2 + 8 * 3, 6 + 8 * 3, 7 + 8 * 3]],
            [[get_gray(140, 20), outline_color], [4 + 8 * 3, 0 + 8 * 3, 3 + 8 * 3, 7 + 8 * 3]],
            [[get_gray(140, 20), outline_color], [1 + 8 * 3, 5 + 8 * 3, 6 + 8 * 3, 2 + 8 * 3]],
            # orb TL
            [[get_red(140, 20), outline_color], [0 + 8 * 4, 1 + 8 * 4, 2 + 8 * 4, 3 + 8 * 4]],
            [[get_red(140, 20), outline_color], [4 + 8 * 4, 5 + 8 * 4, 1 + 8 * 4, 0 + 8 * 4]],
            [[get_red(140, 20), outline_color], [5 + 8 * 4, 4 + 8 * 4, 7 + 8 * 4, 6 + 8 * 4]],
            [[get_red(140, 20), outline_color], [3 + 8 * 4, 2 + 8 * 4, 6 + 8 * 4, 7 + 8 * 4]],
            [[get_red(140, 20), outline_color], [4 + 8 * 4, 0 + 8 * 4, 3 + 8 * 4, 7 + 8 * 4]],
            [[get_red(140, 20), outline_color], [1 + 8 * 4, 5 + 8 * 4, 6 + 8 * 4, 2 + 8 * 4]],
        ],
        (window.width / 2, window.height / 2), mult, 2, 0, 0, 0, 0, 0.015, 0,
    )
    return hammer


def get_tool_crafter():
    tool_crafter_img = tpgb.imgload3("Images", "Midblits", "tool-crafter.png")
    w, h = 550, 350
    tool_crafter_img = pygame.Surface((w, h), pygame.SRCALPHA)
    pgb.draw_rect(tool_crafter_img, (*NAVY_BLUE[:3], 220), (0, 0, w, h))
    pgb.draw_rect(tool_crafter_img, NAVY_BLUE, (0, 0, tool_crafter_sword_width, h))
    pgb.draw_rect(tool_crafter_img, BLACK, (0, 0, w, h), 3)
    pgb.draw_rect(tool_crafter_img, BLACK, (0, 0, tool_crafter_sword_width, h), 3)
    # pgb.write(tool_crafter_img, "topleft", "wt% Fe", orbit_fonts[16], BLACK, 136, 8)
    # pgb.write(tool_crafter_img, "topleft", "wt% C", orbit_fonts[16], BLACK, 220, 8)
    pygame.image.save(tool_crafter_img, path("Images", "Surfaces", "tool-crafter.png"))


def get_compos(name, mult=compos_mult, unlocked=True):
    hard = hagane if unlocked else (20, 20, 20, 255)
    medium = kawagane if unlocked else (40, 40, 40, 255)
    soft = shigane if unlocked else (60, 60, 60, 255)
    compos = getattr(current_module, f"get_{name}")(mult, hard, medium, soft)
    return compos


def get_maru(mult, hard, medium, soft):
    w = 0.1
    lu = w * 2
    ld = lu * 1.3
    t = w * 0.5
    outline_color = BLACK
    maru = Crystal(
        window.display, [
            [0, -lu - t, 0],
            [w, -lu, 0],
            [w, 0, 0],
            [0, ld, 0],
            [-w, 0, 0],
            [-w, -lu, 0],
        ], [
            # point colors
        ], [
            # connections
            [outline_color, 0, 1],
            [outline_color, 1, 2],
            [outline_color, 2, 3],
            [outline_color, 3, 4],
            [outline_color, 4, 5],
            [outline_color, 5, 0],
        ], [
            # fills
            [[hard, hard], [0, 1, 2, 3]],
            [[hard, hard], [3, 4, 5, 0]],
        ],
        (window.width / 2, window.height / 2), mult, 2, 0, 0, 0, 0, compos_yvel, 0,
        target_oox=0,
        target_m=compos_mult,
        speed=compos_speed,
    )
    return maru


def get_kobuse(mult, hard, medium, soft):
    w = 0.1
    lu = w * 2
    ld = lu * 1.3
    t = w * 0.5
    outline_color = BLACK
    kobuse = Crystal(
        window.display, [
            # base
            [0, -lu - t, 0],
            [w, -lu, 0],
            [w, 0, 0],
            [0, ld, 0],
            [-w, 0, 0],
            [-w, -lu, 0],
            # inside
            [w * 0.5, -lu - t * 0.5, 0],
            [w * 0.5, 0, 0],
            [0, ld * 0.5, 0],
            [-w * 0.5, 0, 0],
            [-w * 0.5, -lu - t * 0.5, 0],
        ], [
            # point colors
        ], [
            # connections
            [outline_color, 0, 1],
            [outline_color, 1, 2],
            [outline_color, 2, 3],
            [outline_color, 3, 4],
            [outline_color, 4, 5],
            [outline_color, 5, 0],
            [outline_color, 6, 7],
            [outline_color, 7, 8],
            [outline_color, 8, 9],
            [outline_color, 9, 10],
        ], [
            # fills
            # base
            [[hard, hard], [6, 1, 2, 7]],
            [[hard, hard], [7, 2, 3, 8]],
            [[hard, hard], [8, 3, 4, 9]],
            [[hard, hard], [5, 10, 9, 4]],
            [[soft, soft], [0, 6, 7, 8]],
            [[soft, soft], [0, 8, 9, 10]],
        ],
        (window.width / 2, window.height / 2), mult, 2, 0, 0, 0, 0, compos_yvel, 0,
        target_oox=0,
        target_m=compos_mult,
        speed=compos_speed,
    )
    return kobuse


def get_honsanmai(mult, hard, medium, soft):
    w = 0.1
    lu = w * 2
    ld = lu * 1.3
    t = w * 0.5
    rc = ld / w
    outline_color = BLACK
    honsanmai = Crystal(
        window.display, [
            # base
            [0, -lu - t, 0],
            [w, -lu, 0],
            [w, 0, 0],
            [0, ld, 0],
            [-w, 0, 0],
            [-w, -lu, 0],
            # inside
            [w * 0.5, -lu - t * 0.5, 0],
            [w * 0.5, 0, 0],
            [w * 0.5, w * 0.5 * rc, 0],
            [-w * 0.5, w * 0.5 * rc, 0],
            [-w * 0.5, 0, 0],
            [-w * 0.5, -lu - t * 0.5, 0],
        ], [
            # point colors
        ], [
            # connections
            [outline_color, 0, 1],
            [outline_color, 1, 2],
            [outline_color, 2, 3],
            [outline_color, 3, 4],
            [outline_color, 4, 5],
            [outline_color, 5, 0],
            [outline_color, 6, 8],
            [outline_color, 11, 9],
            [outline_color, 10, 7],
        ], [
            # fills
            # base
            [[medium, medium], [6, 1, 2, 8]],
            [[hard, hard], [10, 7, 8, 9]],
            [[hard, hard], [9, 8, 3]],
            [[medium, medium], [5, 11, 9, 4]],
            [[soft, soft], [11, 6, 7, 10]],
            [[soft, soft], [0, 6, 11]],

        ],
        (window.width / 2, window.height / 2), mult, 2, 0, 0, 0, 0, compos_yvel, 0,
        target_oox=0,
        target_m=compos_mult,
        speed=compos_speed,
    )
    return honsanmai


def get_shihozume(mult, hard, medium, soft):
    w = 0.1
    lu = w * 2
    ld = lu * 1.3
    t = w * 0.5
    rc = ld / w
    outline_color = BLACK
    shihozume = Crystal(
        window.display, [
            # base
            [0, -lu - t, 0],
            [w, -lu, 0],
            [w, 0, 0],
            [0, ld, 0],
            [-w, 0, 0],
            [-w, -lu, 0],
            # inside
            [w * 0.5, -lu - t * 0.5, 0],
            [w * 0.5, -lu + t * 0.5, 0],
            [w * 0.5, w * 0.5 * rc, 0],
            [-w * 0.5, w * 0.5 * rc, 0],
            [-w * 0.5, -lu + t * 0.5, 0],
            [-w * 0.5, -lu - t * 0.5, 0],
        ], [
            # point colors
        ], [
            # connections
            [outline_color, 0, 1],
            [outline_color, 1, 2],
            [outline_color, 2, 3],
            [outline_color, 3, 4],
            [outline_color, 4, 5],
            [outline_color, 5, 0],
            [outline_color, 6, 8],
            [outline_color, 11, 9],
            [outline_color, 10, 7],
        ], [
            # fills
            # base
            [[medium, medium], [6, 1, 2, 8]],
            [[soft, soft], [10, 7, 8, 9]],
            [[hard, hard], [9, 8, 3]],
            [[medium, medium], [5, 11, 9, 4]],
            [[medium, medium], [11, 6, 7, 10]],
            [[medium, medium], [0, 6, 11]],

        ],
        (window.width / 2, window.height / 2), mult, 2, 0, 0, 0, 0, compos_yvel, 0,
        # target_oox=0,
        # target_m=compos_mult,
        speed=compos_speed,
    )
    return shihozume


def get_makuri(mult, hard, medium, soft):
    w = 0.1
    lu = w * 2
    ld = lu * 1.3
    t = w * 0.5
    outline_color = BLACK
    makuri = Crystal(
        window.display, [
            # base
            [0, -lu - t, 0],
            [w, -lu, 0],
            [w, 0, 0],
            [0, ld, 0],
            [-w, 0, 0],
            [-w, -lu, 0],
            # inside
            [w * 0.5, -lu + t * 0.5, 0],
            [w * 0.5, 0, 0],
            [0, ld * 0.5, 0],
            [-w * 0.5, 0, 0],
            [-w * 0.5, -lu + t * 0.5, 0],
            [0, -lu, 0]
        ], [
            # point colors
        ], [
            # connections
            [outline_color, 0, 1],
            [outline_color, 1, 2],
            [outline_color, 2, 3],
            [outline_color, 3, 4],
            [outline_color, 4, 5],
            [outline_color, 5, 0],
            [outline_color, 6, 7],
            [outline_color, 7, 8],
            [outline_color, 8, 9],
            [outline_color, 9, 10],
        ], [
            # fills
            # base
            [[hard, hard], [6, 1, 2, 7]],
            [[hard, hard], [7, 2, 3, 8]],
            [[hard, hard], [4, 9, 8, 3]],
            [[hard, hard], [5, 10, 9, 4]],
            [[hard, hard], [0, 1, 6, 11]],
            [[hard, hard], [5, 0, 11, 10]],
            [[soft, soft], [11, 6, 7, 8]],
            [[soft, soft], [10, 11, 8, 9]],
        ],
        (window.width / 2, window.height / 2), mult, 2, 0, 0, 0, 0, compos_yvel, 0,
        target_oox=0,
        target_m=compos_mult,
        speed=compos_speed,
    )
    return makuri
