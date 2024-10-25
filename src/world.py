import opensimplex as osim
from enum import Enum
#
from pyengine.pgbasics import *
#
from .engine import *
from . import blocks
from . import fonts


CW = 16
CH = 16


class World:
    def __init__(self):
        self.data = {}
        self.chunk_surfaces = {}
        self.chunk_colors = {}
        self.scroll = [0, 0]
        self.create_world()
    
    def create_world(self):
        self.data = {}
    
    def create_chunk(self, chunk_pos):
        # initialize empty chunk data
        chunk_x, chunk_y = chunk_pos
        self.data[chunk_pos] = {}
        self.chunk_surfaces[chunk_pos] = pygame.Surface((CW * BS, CH * BS), pygame.SRCALPHA)
        self.chunk_colors[chunk_pos] = [rand(0, 255) for _ in range(3)]
        # generate the chunk
        for rel_y in range(CH):
            for rel_x in range(CW):
                # init variables
                blit_x, blit_y = rel_x * BS, rel_y * BS
                block_x, block_y = chunk_x * CW + rel_x, chunk_y * CH + rel_y
                if chunk_y < -1:
                    # SKY
                    name = "air"
                elif chunk_y == -1:
                    # SURFACE LEVEL
                    name = "air"
                    noise = int(osim.noise2(x=block_x * 0.08, y=0) * 8)
                    if rel_y == CH / 2 + noise:
                        name = "soil_f"
                    elif rel_y > CH / 2 + noise:
                        name = "dirt_f"
                else:
                    # UNDERGROUND
                    name = "stone" if osim.noise2(x=block_x * 0.08, y=block_y * 0.08) < 0 else "air"
                self.data[chunk_pos][(rel_x, rel_y)] = name
                self.chunk_surfaces[chunk_pos].blit(blocks.images[name], (blit_x, blit_y))

    def update(self, display):
        m = 2.5
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.scroll[0] -= m
        if keys[pygame.K_d]:
            self.scroll[0] += m
        if keys[pygame.K_w]:
            self.scroll[1] -= m
        if keys[pygame.K_s]:
            self.scroll[1] += m
     
        for yo in range(-3, 4):
            for xo in range(-3, 4):
                # init
                chunk_x = xo - 1 + int(round(self.scroll[0] / (CW * BS)))
                chunk_y = yo - 1 + int(round(self.scroll[1] / (CH * BS)))
                chunk_pos = (chunk_x, chunk_y)
                # create chunk in case it doesnt' exist yet
                if chunk_pos not in self.data:
                    self.create_chunk(chunk_pos)
                # render the shunk surface
                chunk_topleft = chunk_pos[0] * CW * BS - self.scroll[0], chunk_pos[1] * CH * BS - self.scroll[1]
                chunk_rect = pygame.Rect((*chunk_topleft, CW * BS, CH * BS))
                surf = self.chunk_surfaces[chunk_pos]
                display.blit(surf, chunk_topleft)
                pygame.draw.rect(display, self.chunk_colors[chunk_pos], chunk_rect, 1)
                write(display, "center", chunk_pos, fonts.orbitron[20], (0, 0, 0), *chunk_rect.center)
