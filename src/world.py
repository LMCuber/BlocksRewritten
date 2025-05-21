import opensimplex as osim
from enum import Enum
from collections import deque
import uuid
#
from pyengine.pgbasics import *
from pyengine.ecs import *
#
from .engine import *
from .window import *
from .entities import *
from .blocks import (
    BF, bwand, nbwand, MAX_LIGHTING
)
from . import fonts
from . import blocks


class Biome(Enum):
    FOREST = auto()
    MOUNTAIN = auto()
    BEACH = auto()


@dataclass
class BiomeData:
    blocks = {
        # cherry on top, main block, subblock
        Biome.FOREST: ("soil_f", "dirt_f"),
        Biome.MOUNTAIN: ("snow-stone", "stone"),
        Biome.BEACH: ("sand", "sand"),
    }


bio = BiomeData()


@dataclass
class Breaking:
    index: tuple[int, int] | None = None
    pos: tuple[int, int] | None = None
    anim: int = 0


class World:
    def __init__(self, menu):
        self.menu = menu

        self.data = {}
        self.late_data = {}
        self.bg_data = {}
        self.chunk_surfaces = {}
        self.chunk_colors = {}
        self.lightmap = {}
        self.light_surfaces = {}

        # world interactive stuff
        self.breaking = Breaking()

        self.create_world()
        self.seed = uuid.uuid4().int
        osim.seed(self.seed)
        self.random = random.Random(self.seed)

        # misc
        self.lates = []
    
    def bnorm(self, name: str) -> (str, list[str]):
        """
        Returns the normalized version of a block name, devoid of all modifiers e.g. stone|b (background stone) -> stone
        Normalized values are split by pipes.
        Quick check to know whether a fragmentation should be a norm or pure: if it has its own image and data, its a norm (e.g. tree_f has an image but tree_f|b does not)
        """
        spl = name.split("|")
        base = spl[0]
        mods = spl[1:]
        return base, mods

    def bpure(self, name: str) -> (str, str, str, list[str]):
        """
        Returns the pure version, as well as the normalized version, of a block which is its most important part. This is to make sure that for e.g. tree_f and tree_p don't get differentiated.
        Pure values are split by underscores.
        """
        base, mods = self.bnorm(name)
        spl = base.split("_")
        pure = spl[0]
        vers = spl[1:]
        return pure, spl, base, mods
    
    def get_radius_around(self, radius):
        offsets = []
        r_squared = radius ** 2
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                dist_sq = dx*dx + dy*dy
                if dist_sq <= r_squared:
                    offsets.append((dist_sq, dx, dy))
        
        offsets.sort()
        
        return [(dx, dy) for _, dx, dy in offsets]
    
    def exists(self, chunk_index, block_pos):
        return chunk_index in self.data and block_pos in self.data[chunk_index]
    
    def break_(self, chunk_index, block_pos):
        base, mods = self.bnorm(self.data[chunk_index][block_pos])
        if "b" not in mods:
            if block_pos in self.bg_data[chunk_index]:
                self.set(chunk_index, block_pos, self.bg_data[chunk_index][block_pos])
            else:
                del self.data[chunk_index][block_pos]
    
    def get_blocks_around(self, rect, range_x=(-1, 1), range_y=(-1, 1), return_name=False):
        og_chunk_index, og_block_pos = self.pos_to_tile(rect.center)
        for yo in range(range_y[0], range_y[1] + 1):
            for xo in range(range_x[0], range_x[1] + 1):
                chunk_index, block_pos = self.correct_tile(og_chunk_index, og_block_pos, xo, yo)
                if chunk_index in self.data and block_pos in self.data[chunk_index]:
                    name = self.data[chunk_index][block_pos]
                    block_rect = pygame.Rect(block_pos[0] * BS, block_pos[1] * BS, BS, BS)
                    base, mods = self.bnorm(name)
                    if return_name:
                        yield (block_rect, base)
                    else:
                        if all(x not in mods for x in ["b", "B"]) and nbwand(base, BF.WALKABLE):
                            yield block_rect
    
    def screen_pos_to_tile(self, pos, scroll):
        x, y = pos
        # x and y must be unscaled and unscrolled; returns chunk and abs_pos ([chunk][pos] notation for accessation :D :P :/ :] Ü)
        target_x = floor(x / (BS * CW) + scroll[0] / (BS * CW))
        target_y = floor(y / (BS * CH) + scroll[1] / (BS * CH))
        target_chunk = (target_x, target_y)
        abs_x = floor(x / BS + scroll[0] / BS)
        abs_y = floor(y / BS + scroll[1] / BS)
        abs_pos = (abs_x, abs_y)
        return target_chunk, abs_pos

    def tile_to_screen_pos(self, abs_pos, scroll):
        abs_x, abs_y = abs_pos
        screen_x = (abs_x - scroll[0]) * BS
        screen_y = (abs_y - scroll[1]) * BS
        return screen_x, screen_y

    def pos_to_tile(self, pos):
        return ((
                floor(pos[0] / (CW * BS)),
                floor(pos[1] / (CH * BS)),
            ), (
                floor(pos[0] / BS),
                floor(pos[1] / BS),
            )
        )

    def correct_tile(self, chunk_index, block_pos, xo, yo):
        rel_x, rel_y = block_pos[0] % CW, block_pos[1] % CH
        default = True
        pos_xo = xo
        pos_yo = yo
        chunk_xo = chunk_yo = 0
        # correct (verb) (thanks didn't realizzze drizzo) bordering chunks
        if rel_x + xo < 0:
            chunk_xo -= 1
        elif rel_x + xo > CW - 1:
            chunk_xo += 1
        if rel_y + yo < 0:
            chunk_yo -= 1
        elif rel_y + yo > CH - 1:
            chunk_yo += 1
        block_pos = (block_pos[0] + pos_xo, block_pos[1] + pos_yo)
        chunk_index = (chunk_index[0] + chunk_xo, chunk_index[1] + chunk_yo)
        return chunk_index, block_pos

    def octave_noise(self, x, y, freq, amp=1, octaves=1, lac=2, pers=0.5):
        height = 0
        max_value = 0
        for i in range(octaves):
            nx = x * freq
            ny = y * freq
            height += amp * osim.noise2(x=nx, y=ny)

            max_value += amp
            freq *= lac
            amp *= pers

        height = (height + max_value) / (max_value * 2)
        return height

    def create_world(self):
        self.data = {}
    
    def modify_chunk(self, chunk_index):
        def _set(name, mod_pos):
            rel_x, rel_y = mod_pos[0] - chunk_index[0] * CW, mod_pos[1] - chunk_index[1] * CH
            if 0 <= rel_x < CW and 0 <= rel_y < CH:
                self.set(chunk_index, mod_pos, name)
            else:
                xo = mod_pos[0] - block_pos[0]
                yo = mod_pos[1] - block_pos[1]
                new_chunk_index, new_block_pos = self.correct_tile(chunk_index, block_pos, xo, yo)
                if new_chunk_index in self.late_data:
                    self.late_data[new_chunk_index][new_block_pos] = name
                else:
                    self.late_data[new_chunk_index] = {new_block_pos: name}
        
        def _get(mod_pos):
            rel_x, rel_y = mod_pos[0] - chunk_index[0] * CW, mod_pos[1] - chunk_index[1] * CH
            if 0 <= rel_x < CW and 0 <= rel_y < CH:
                try:
                    return self.data[chunk_index][mod_pos]
                except KeyError:
                    return "air"
            else:
                xo = mod_pos[0] - block_pos[0]
                yo = mod_pos[1] - block_pos[1]
                new_chunk_index, new_block_pos = self.correct_tile(chunk_index, block_pos, xo, yo)
                try:
                    return self.data[new_chunk_index][new_block_pos]
                except KeyError:
                    return None

        _chance = lambda p: self.random.random() < p
        _rand = lambda a, b: self.random.randint(a, b)
        _nordis = lambda mu, sigma: int(self.random.gauss(mu, sigma))
        _choice = lambda x: self.random.choice(x)

        biome = Biome.FOREST

        chunk_x, chunk_y = chunk_index
        _spawned = False
        for rel_y in range(CH):
            for rel_x in range(CW):
                # init
                blit_x, blit_y = rel_x * BS, rel_y * BS
                block_pos = block_x, block_y = chunk_x * CW + rel_x, chunk_y * CH + rel_y
                name = og_name = self.data[chunk_index].get(block_pos, None)

                # topmost block (soil or something)
                if name == bio.blocks[biome][0] and _get((block_x, block_y - 1)) == "air":
                    # forest modifications
                    if biome == Biome.FOREST:
                        # entitites
                        if not _spawned and False and chunk_index == (0, 0) and _chance(1 / 5):
                            create_entity(
                                Transform([0, 0], [2.1, 0], flag=TransformFlag(TransformFlags.MOB), gravity=0.03),
                                Hitbox((block_pos[0] * BS, block_pos[1] * BS - BS * 6), (0, 0), anchor="midbottom"),
                                Sprite.from_path(Path("res", "images", "mobs", "bok-bok", "walk.png")),
                                PlayerFollower(0),
                                Headbutter(30),
                                chunk=chunk_index
                            )
                            _spawned = True
                        if _chance(1 / 20):
                            create_entity(
                                Transform([0, 0], [0, 0], gravity=0.08),
                                Hitbox((block_pos[0] * BS, block_pos[1] * BS - BS * 6), (100, 100), anchor="midbottom"),
                                Sprite.from_path(Path("res", "images", "spritesheets", "statics", "portal", "idle.png")),
                                chunk=chunk_index
                            )
                        # forest tree
                        if _chance(1 / 24):
                            # tree_height = _rand(10, 14)
                            tree_height = _nordis(9, 2)
                            for tree_yo in range(tree_height):
                                wood_x, wood_y = block_x, block_y - tree_yo - 1
                                wood_suffix = ""
                                leaf_name = "leaf_f"
                                leaf_chance = 1 / 2.4
                                if tree_yo > 0:
                                    if _chance(leaf_chance):
                                        wood_suffix += "L"
                                        _set(leaf_name, (wood_x - 1, wood_y))
                                    if _chance(leaf_chance):
                                        wood_suffix += "R"
                                        _set(leaf_name, (wood_x + 1, wood_y))
                                    if tree_yo == tree_height - 1:
                                        wood_suffix += "T"
                                        _set(leaf_name, (wood_x, wood_y - 1))
                                wood_suffix = "N" if not wood_suffix else wood_suffix
                                wood_name = f"wood_f_vr{wood_suffix}"
                                _set(wood_name, (wood_x, wood_y))
                    
                    elif biome == Biome.BEACH:
                        # rock
                        if _chance(1 / 15):
                            _set("rock|b", (block_x, block_y - 1))

                        # beach tree
                        if _chance(1 / 24):
                            # tree stem
                            tree_height = _nordis(9, 2)
                            for tree_yo in range(tree_height):
                                wood_x, wood_y = block_x, block_y - tree_yo - 1
                                _set("wood_p", (wood_x, wood_y))
                            leaf_x, leaf_y = wood_x, wood_y
                            # trees
                            _set("leaf_f", (wood_x - 1, wood_y))
                            _set("leaf_f", (wood_x, wood_y - 1))
                            _set("leaf_f", (wood_x + 1, wood_y))

                # update chunk data and blit block image
                if name != og_name:
                    self.set(chunk_index, block_pos, name)
    
    def set(self, chunk_index, block_pos, name):
        self.data[chunk_index][block_pos] = name
        if name == "dynamite":
            self.lightmap[chunk_index][block_pos] = MAX_LIGHTING
            self.update_lighting(chunk_index, block_pos)
        else:
            self.lightmap[chunk_index][block_pos] = 0
    
    def create_chunk(self, chunk_index):
        # initialize new chunk data in RAM
        chunk_x, chunk_y = chunk_index
        self.data[chunk_index] = {}
        self.chunk_colors[chunk_index] = [rand(0, 255) for _ in range(3)]
        self.bg_data[chunk_index] = {}
        self.lightmap[chunk_index] = {}
        self.light_surfaces[chunk_index] = pygame.Surface((CW * BS, CH * BS), pygame.SRCALPHA)
        biome = Biome.FOREST

        # generate the chunk
        for rel_y in range(CH):
            for rel_x in range(CW):
                # init variables
                blit_x, blit_y = rel_x * BS, rel_y * BS
                block_x, block_y = chunk_x * CW + rel_x, chunk_y * CH + rel_y

                # chunks 0 and 1 need 1D noise for terrain height
                if chunk_y in (0, 1):
                    offset = int(self.octave_noise(block_x, 0, 0.04) * CW)

                if chunk_y < 0:
                    # SKY
                    name = "air"
                elif chunk_y == 0:
                    # GROUND LEVEL
                    if rel_y == offset:
                        # top block in a biome
                        name = bio.blocks[biome][0]
                        if name == "soil_f":
                            self.bg_data[chunk_index][(block_x, block_y)] = f"dirt_f|b"
                        else:
                            self.bg_data[chunk_index][(block_x, block_y)] = f"{name}|b"
                    elif rel_y < offset:
                        # air
                        name = "air"
                    else:
                        # underground blocks
                        name = bio.blocks[biome][1]
                        self.bg_data[chunk_index][(block_x, block_y)] = f"{name}|b"
                elif chunk_y == 1:
                    # DIRT-CAVE HYBRID
                    if rel_y <= offset:
                        name = bio.blocks[biome][1]
                        self.bg_data[chunk_index][(block_x, block_y)] = f"{name}|b"
                    else:
                        name = "stone"
                        self.bg_data[chunk_index][(block_x, block_y)] = f"{name}|b"
                    
                    base, mods = self.bnorm(name)
                else:
                    # UNDERGROUND
                    name = "stone|b" if self.octave_noise(block_x, block_y, freq=0.04, octaves=3, lac=2) < 0.46 else "stone"
                    self.bg_data[chunk_index][(block_x, block_y)] = f"{name}|b"

                if name != "air":
                    self.set(chunk_index, (block_x, block_y), name)

        self.modify_chunk(chunk_index)
        # self.update_lighting(chunk_index)
    
    def update_lighting(self, chunk_index, block_pos=None):
        # initialize data structures
        queue = deque()
        visited = set()

        # check if a given light block is given or there is no information about what is light
        if block_pos is None:
            for block_pos in self.data[chunk_index]:
                if self.data[chunk_index][block_pos] == "dynamite":
                    queue.append((chunk_index, block_pos, 10))  # (chunk_index, block_pos, light)
        else:
            queue.append((chunk_index, block_pos, 10))

        # define the directions of propagation
        offsets = [(1, 0), (0, 1), (-1, 0), (0, -1)]

        # work through the queue
        n = 0
        while queue:
            chunk_index, block_pos, light = queue.popleft()
            block_x, block_y = block_pos

            # check whether this particular block is air
            if chunk_index not in self.lightmap or block_pos not in self.lightmap[chunk_index]:
                # air, so no operation
                continue

            # check if newly calculated light value is higher than what is already there
            if light < self.lightmap[chunk_index][block_pos]:
                continue

            # skip if block has already been visited
            if (chunk_index, block_pos) in visited:
                continue

            # update the lighting texture
            n += 1
            self.lightmap[chunk_index][block_pos] = light
            light_color = (MAX_LIGHTING - light) / MAX_LIGHTING * 255
            blit_pos = (block_pos[0] % CW * BS, block_pos[1] % CH * BS)
            pygame.draw.rect(self.light_surfaces[chunk_index], (0, 0, 0, light_color), (*blit_pos, BS, BS))
            visited.add((chunk_index, block_pos))

            # still apply but don't propagate zero value light
            if light <= 0:
                continue

            for (xo, yo) in offsets:
                nei_chunk_index, nei_block_pos = self.correct_tile(chunk_index, block_pos, xo, yo)
                queue.append((nei_chunk_index, nei_block_pos, light - 1))
        
        print(n)
        
    def update(self, display, scroll):
        # lates
        for pos in self.lates:
            pygame.draw.aacircle(display, RED, pos, 3)

        # actual
        num_blocks = 0
        processed_chunks = []
        block_rects = []

        # clear the lightmap
        # self.lightmap.fill(BLACK)

        HOR_CHUNK_DISTANCE = 3
        VER_CHUNK_DISTANCE = 4
        for yo in range(HOR_CHUNK_DISTANCE):
            for xo in range(VER_CHUNK_DISTANCE):
                # get chunk coordinates from game scroll
                chunk_x = xo - 1 + int(round(scroll[0] / (CW * BS)))
                chunk_y = yo - 1 + int(round(scroll[1] / (CH * BS)))
                chunk_index = (chunk_x, chunk_y)

                # create chunk in case it does not exist yet
                if chunk_index not in self.data:
                    self.create_chunk(chunk_index)

                # check whether it is just late
                if chunk_index in self.late_data:
                    for block_pos, name in self.late_data[chunk_index].copy().items():
                        self.set(chunk_index, block_pos, name)
                        del self.late_data[chunk_index][block_pos]

                # render the shunk surface
                chunk_topleft = chunk_index[0] * CW * BS - scroll[0], chunk_index[1] * CH * BS - scroll[1]
                chunk_rect = pygame.Rect((*chunk_topleft, CW * BS, CH * BS))

                for (block_x, block_y), name in self.data[chunk_index].items():
                    blit_pos = (block_x * BS - scroll[0], block_y * BS - scroll[1])

                    # process block modifications
                    base, mods = self.bnorm(name)
                    if "b" in mods:
                        image = blocks.images[f"{base}|b"]
                    else:
                        image = blocks.images[base]

                    # ! render block !
                    display.blit(image, blit_pos)
                    
                    # add a block that can be interacted with
                    block_rects.append(pygame.Rect(*blit_pos, BS, BS))
                    num_blocks += 1

                # ! render lights !
                display.blit(self.light_surfaces[chunk_index], chunk_rect)

                if self.menu.chunk_borders.checked:
                    pygame.draw.rect(display, self.chunk_colors[chunk_index], chunk_rect, 1)
                    write(display, "center", chunk_index, fonts.orbitron[20], (0, 0, 0), *chunk_rect.center)

                processed_chunks.append(chunk_index)

        # show the breaking block
        if (self.breaking.index, self.breaking.pos) != (None, None):
            breaking_pos = (self.breaking.pos[0] * BS - scroll[0], self.breaking.pos[1] * BS - scroll[1])
            # check if the breaking actually breaks
            try:
                blocks.breaking_sprs[int(self.breaking.anim)]
            except IndexError:
                # drop the item
                self.drop()
                # break the block
                del self.data[self.breaking.index][self.breaking.pos]
                # reset the breaking
                self.breaking.index = None
                self.breaking.pos = None
            else:
                # render the block breaking spritesheet
                display.blit(blocks.breaking_sprs[int(self.breaking.anim)], breaking_pos)

        # return information
        return num_blocks, processed_chunks, block_rects

    def drop(self):
        # coordinates for the drop
        x = self.breaking.pos[0] * BS + BS / 2
        y = self.breaking.pos[1] * BS + BS / 2
        # block image
        base, _ = self.bnorm(self.data[self.breaking.index][self.breaking.pos])
        # modify the dropped image so it distinguished itself form its environment
        drop_img = pygame.transform.scale_by(blocks.images[base], 0.5)
        if not (bwand(base, BF.NONSQUARE)):
            pygame.draw.rect(drop_img, BLACK, (0, 0, *drop_img.size), 1)
        #
        # create_entity(
        #     Transform([x - BS / 4 + rand(-5, 5), y - BS / 4 + rand(-5, 5)], [0, 0], gravity=0.03, sine=(0.35, 4)),
        #     Sprite.from_img(drop_img),
        #     Drop(base),
        #     chunk=0
        # )
