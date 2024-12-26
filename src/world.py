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


class World:
    def __init__(self):
        self.ecs_container = {}
        self.data = {}
        self.late_data = {}
        self.chunk_surfaces = {}
        self.chunk_colors = {}
        self.create_world()
        self.seed = uuid.uuid4().int
        # self.seed = 123
        osim.seed(self.seed)
        self.random = random.Random(self.seed)

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
        self.ecs_container = {}
    
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

        _chance = lambda p: self.random.random() < p
        _rand = lambda a, b: self.random.randint(a, b)

        chunk_x, chunk_y = chunk_index
        for rel_y in range(CH):
            for rel_x in range(CW):
                # init
                blit_x, blit_y = rel_x * BS, rel_y * BS
                block_pos = block_x, block_y = chunk_x * CW + rel_x, chunk_y * CH + rel_y
                name = og_name = self.data[chunk_index].get(block_pos, None)
                # modify!
                if name == "soil_f":
                    # create_entity(
                    #     Transform([block_pos[0] * BS, (block_pos[1] - 2) * BS], [randf(0, 0), 0.0], glob.gravity*0),
                    #     Sprite(Path("res", "images", "mobs", "penguin", "walk.png"), 4, 0.1),
                    #     PlayerFollower(acc=True),
                    #     chunk=chunk_index,
                    # )
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
                # update chunk data and blit block image
                if name != og_name:
                    self.data[chunk_index][block_pos] = name
                if name is not None:
                    self.chunk_surfaces[chunk_index].blit(blocks.images[name], (blit_x, blit_y))
    
    def create_chunk(self, chunk_index):
        # initialize empty chunk data
        chunk_x, chunk_y = chunk_index
        self.data[chunk_index] = {}
        self.chunk_surfaces[chunk_index] = pygame.Surface((CW * BS, CH * BS), pygame.SRCALPHA)
        self.chunk_colors[chunk_index] = [rand(0, 255) for _ in range(3)]
        # initialize empty entity component system
        # self.ecs_container[chunk_index] = {ECS()}
        # generate the chunk
        for rel_y in range(CH):
            for rel_x in range(CW):
                # init variables
                blit_x, blit_y = rel_x * BS, rel_y * BS
                block_x, block_y = chunk_x * CW + rel_x, chunk_y * CH + rel_y
                if chunk_y in (-1, 0):
                    # input, dispersion
                    noise = int(osim.noise2(x=block_x * 0.01, y=0) * 8)
                if chunk_y < -1:
                    # SKY
                    name = "air"
                elif chunk_y == -1:
                    # SURFACE LEVEL
                    name = "air"
                    if rel_y == CH / 2 + noise:
                        name = "soil_f"
                    elif rel_y > CH / 2 + noise:
                        name = "dirt_f"
                elif chunk_y == 0:
                    # SOIL UNDER SURFACE LEVEL
                    if rel_y > CH / 2 + noise:
                        name = "stone"
                    else:
                        name = "dirt_f"
                else:
                    # UNDERGROUND
                    name = "stone" if osim.noise2(x=block_x * 0.08, y=block_y * 0.08) < 0 else "air"
                if name != "air":
                    self.data[chunk_index][(block_x, block_y)] = name
        self.modify_chunk(chunk_index)
    
    def update(self, display, scroll):
        num_blocks = 0
        processed_chunks = []
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
                #display.blit(surf, chunk_topleft)
                pygame.draw.rect(display, self.chunk_colors[chunk_index], chunk_rect, 1)
                write(display, "center", chunk_index, fonts.orbitron[20], (0, 0, 0), *chunk_rect.center)
                #
                processed_chunks.append(chunk_index)
        return num_blocks, processed_chunks
