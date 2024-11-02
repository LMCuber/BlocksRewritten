import opensimplex as osim
from enum import Enum
import uuid
#
from pyengine.pgbasics import *
#
from .engine import *
from . import fonts
from .window import *
from . import blocks


CW = 16
CH = 16


class World:
    def __init__(self):
        self.data = {}
        self.chunk_surfaces = {}
        self.chunk_colors = {}
        self.create_world()
        self.seed = uuid.uuid4().int
        self.seed = 123
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

    def correct_tile(self, target_chunk, block_pos, xo, yo):
        rel_x, rel_y = block_pos[0] % CW, block_pos[1] % CH
        default = True
        pos_xo = xo
        pos_yo = yo
        chunk_xo = chunk_yo = 0
        # correct (verb) (thanks didn't realizzze) bordering chunks
        if rel_x + xo < 0:
            chunk_xo -= 1
        elif rel_x + xo > CW - 1:
            chunk_xo += 1
        if rel_y + yo < 0:
            chunk_yo -= 1
        elif rel_y + yo > CH - 1:
            chunk_yo += 1
        block_pos = (block_pos[0] + pos_xo, block_pos[1] + pos_yo)
        target_chunk = (target_chunk[0] + chunk_xo, target_chunk[1] + chunk_yo)
        return target_chunk, block_pos
        
    def create_world(self):
        self.data = {}
    
    def modify_chunk(self, chunk_index):
        def _chance(p):
            return self.random.random() < p

        chunk_x, chunk_y = chunk_index
        for rel_y in range(CH):
            for rel_x in range(CW):
                # init
                blit_x, blit_y = rel_x * BS, rel_y * BS
                block_pos = block_x, block_y = chunk_x * CW + rel_x, chunk_y * CH + rel_y
                name = og_name = self.data[chunk_index].get(block_pos, None)
                # modify!
                if name == "soil_f":
                    # tree
                    if _chance(1 / 10):
                        for yo in range(5):
                            tree_y = block_y - yo - 1
                            self.data[chunk_index][block_pos] = name
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
        # generate the chunk
        for rel_y in range(CH):
            for rel_x in range(CW):
                # init variables
                blit_x, blit_y = rel_x * BS, rel_y * BS
                block_x, block_y = chunk_x * CW + rel_x, chunk_y * CH + rel_y
                if chunk_y in (-1, 0):
                    noise = int(osim.noise2(x=block_x * 0.08, y=0) * 8)
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
        for yo in range(-3, 4):
            for xo in range(-3, 4):
                # init
                chunk_x = xo - 1 + int(round(scroll[0] / (CW * BS)))
                chunk_y = yo - 1 + int(round(scroll[1] / (CH * BS)))
                chunk_index = (chunk_x, chunk_y)
                # create chunk in case it doesnt' exist yet
                if chunk_index not in self.data:
                    self.create_chunk(chunk_index)
                # render the shunk surface
     
                chunk_topleft = chunk_index[0] * CW * BS - scroll[0], chunk_index[1] * CH * BS - scroll[1]
                chunk_rect = pygame.Rect((*chunk_topleft, CW * BS, CH * BS))
                surf = self.chunk_surfaces[chunk_index]
                # for (block_x, block_y), name in self.data[chunk_index].items():
                #     blit_pos = (block_x * BS - scroll[0], block_y * BS - scroll[1])
                #     display.blit(blocks.images[name], blit_pos)
                #     num_blocks += 1
                display.blit(surf, chunk_topleft)
                pygame.draw.rect(display, self.chunk_colors[chunk_index], chunk_rect, 1)
                write(display, "center", chunk_index, fonts.orbitron[20], (0, 0, 0), *chunk_rect.center)
        return num_blocks
