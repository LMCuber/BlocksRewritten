import opensimplex as osim
from enum import Enum
import uuid
#
from pyengine.pgbasics import *
from pyengine.ecs import *
#
from .engine import *
from .window import *
from .entities import *
from . import fonts
from . import blocks


CW = 16
CH = 16


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


def octave_noise(x, y, freq, amp=1, octaves=1, lac=1, pers=1):
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


class World:
    def __init__(self, menu):
        self.menu = menu

        self.data = {}
        self.late_data = {}
        self.chunk_surfaces = {}
        self.chunk_colors = {}
        self.chunk_biomes = {}

        self.create_world()
        self.seed = uuid.uuid4().int
        # self.seed = 123
        osim.seed(self.seed)
        self.random = random.Random(self.seed)
        
    def get_blocks_around(self, rect, range_x=(-1, 2), range_y=(-1, 2)):
        og_chunk_index, og_block_pos = self.pos_to_tile(rect.center)
        for yo in range(*range_y):
            for xo in range(*range_x):
                chunk_index, block_pos = self.correct_tile(og_chunk_index, og_block_pos, xo, yo)
                if chunk_index in self.data and block_pos in self.data[chunk_index]:
                    block_rect = pygame.Rect(block_pos[0] * BS, block_pos[1] * BS, BS, BS)
                    yield block_rect
    
    def screen_pos_to_tile(self, pos, scroll):
        x, y = pos
        # x and y must be unscaled & unscrolled; returns chunk and abs_pos ([chunk][pos] notation for accessation :D :P :/ :] Ü)
        target_x = floor(x / (BS * CW) + scroll[0] / (BS * CW))
        target_y = floor(y / (BS * CH) + scroll[1] / (BS * CH))
        target_chunk = (target_x, target_y)
        abs_x = floor(x / BS + scroll[0] / BS)
        abs_y = floor(y / BS + scroll[1] / BS)
        abs_pos = (abs_x, abs_y)
        return target_chunk, abs_pos

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
        
    def create_world(self):
        self.data = {}
    
    def modify_chunk(self, chunk_index):
        def _set(name, mod_pos):
            rel_x, rel_y = mod_pos[0] - chunk_index[0] * CW, mod_pos[1] - chunk_index[1] * CH
            if 0 <= rel_x < CW and 0 <= rel_y < CH:
                self.data[chunk_index][mod_pos] = name
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
                return self.data[new_chunk_index][new_block_pos]

        _chance = lambda p: self.random.random() < p
        _rand = lambda a, b: self.random.randint(a, b)
        _nordis = lambda mu, sigma: int(self.random.gauss(mu, sigma))

        biome = self.chunk_biomes[chunk_index]

        chunk_x, chunk_y = chunk_index
        for rel_y in range(CH):
            for rel_x in range(CW):
                # init
                blit_x, blit_y = rel_x * BS, rel_y * BS
                block_pos = block_x, block_y = chunk_x * CW + rel_x, chunk_y * CH + rel_y
                name = og_name = self.data[chunk_index].get(block_pos, None)
<<<<<<< HEAD
                # modify!
                if name == "soil_f":
                    if _chance(1 / 20):
                        create_entity(
                            Transform([block_pos[0] * BS, (block_pos[1] - 2) * BS], [randf(0, 0.5), 0.0], TransformFlag(TransformFlags.MOB), 0.1),
                            Sprite(Path("res", "images", "mobs", "penguin", "walk.png"), 4, randf(0.01, 0.07)),
                            CollisionFlag(CollisionFlags.RECV),
                            Health(100),
                            PlayerFollower(),
                            chunk=chunk_index
                        )
                    # tree
                    if _chance(1 / 24):
                        tree_height = _rand(6, 8)
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
=======

                # topmost block (soil or something)
                if name == bio.blocks[biome][0] and _get((block_x, block_y - 1)) == "air":
                    # forest modifications
                    if biome == Biome.FOREST:
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
                            _set("rock", (block_x, block_y - 1))
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

>>>>>>> d22e9dcf829be15c2a3f215d41920abdc6aee8d8
                # update chunk data and blit block image
                if name != og_name:
                    self.data[chunk_index][block_pos] = name
                if name is not None:
                    self.chunk_surfaces[chunk_index].blit(blocks.images[name], (blit_x, blit_y))
    
    def create_chunk(self, chunk_index):
        # initialize empty chunk data
        chunk_x, chunk_y = chunk_index
        self.data[chunk_index] = {}
        self.chunk_biomes[chunk_index] = Biome.BEACH
        self.chunk_surfaces[chunk_index] = pygame.Surface((CW * BS, CH * BS), pygame.SRCALPHA)
        self.chunk_colors[chunk_index] = [rand(0, 255) for _ in range(3)]
        biome = self.chunk_biomes[chunk_index]
        # initialize empty entity component system
        # generate the chunk
        for rel_y in range(CH):
            for rel_x in range(CW):
                # init variables
                blit_x, blit_y = rel_x * BS, rel_y * BS
                block_x, block_y = chunk_x * CW + rel_x, chunk_y * CH + rel_y

                # chunks 0 and 1 need noise value for dirt and stone
                if chunk_y in (0, 1):
                    offset = int(octave_noise(block_x, 0, 0.04) * CW)

                if chunk_y < 0:
                    name = "air"
                elif chunk_y == 0:
                    if rel_y == offset:
                        name = bio.blocks[biome][0]
                    elif rel_y < offset:
                        name = "air"
                    else:
                        name = bio.blocks[biome][1]
                elif chunk_y == 1:
                    if rel_y <= offset:
                        name = bio.blocks[biome][1]
                    else:
                        name = "stone"
                else:
                    # UNDERGROUND
                    # name = "stone" if osim.noise2(x=block_x * 0.08, y=block_y * 0.08) < 0 else "air"
                    name = "stone" if octave_noise(block_x, block_y, freq=0.04) < 0.5 else "air"
                if name != "air":
                    self.data[chunk_index][(block_x, block_y)] = name
        self.modify_chunk(chunk_index)
    
    def update(self, display, scroll):
        num_blocks = 0
        processed_chunks = []
        block_rects = []
        for yo in range(3):
            for xo in range(4):
                # init the chunk coordinates and other data
                chunk_x = xo - 1 + int(round(scroll[0] / (CW * BS)))
                chunk_y = yo - 1 + int(round(scroll[1] / (CH * BS)))
                chunk_index = (chunk_x, chunk_y)
                # create chunk in case it does not exist yet
                if chunk_index not in self.data:
                    self.create_chunk(chunk_index)
                # check whether it is just late
                if chunk_index in self.late_data:
                    for block_pos, name in self.late_data[chunk_index].copy().items():
                        self.data[chunk_index][block_pos] = name
                        del self.late_data[chunk_index][block_pos]
                # render the shunk surface
                chunk_topleft = chunk_index[0] * CW * BS - scroll[0], chunk_index[1] * CH * BS - scroll[1]
                chunk_rect = pygame.Rect((*chunk_topleft, CW * BS, CH * BS))
                surf = self.chunk_surfaces[chunk_index]
                for (block_x, block_y), name in self.data[chunk_index].items():
                    blit_pos = (block_x * BS - scroll[0], block_y * BS - scroll[1])
                    display.blit(blocks.images[name], blit_pos)
                    num_blocks += 1
                    # add a block that can be interacted with
                    block_rects.append(pygame.Rect(*blit_pos, BS, BS))
                #display.blit(surf, chunk_topleft)
                pygame.draw.rect(display, self.chunk_colors[chunk_index], chunk_rect, 1)
                write(display, "center", chunk_index, fonts.orbitron[20], (0, 0, 0), *chunk_rect.center)
                #
                processed_chunks.append(chunk_index)
        return num_blocks, processed_chunks, block_rects
