from pathlib import Path
import pygame
from pygame.transform import scale, scale_by
from random import randint as rand
from random import uniform as randf
from random import choice
from math import sin
from dataclasses import dataclass
from math import floor, ceil


S = 3
BS = 10 * S


def cceil(n):
    if n == 0:
        return 0
    elif n > 0:
        return ceil(n)
    else:
        return floor(n)


def inflate_keep(rect, xo, yo=0):
    return rect.inflate(xo, yo).move(xo, yo)


def get_blocks_around(rect, world, range_x=(-1, 2), range_y=(-1, 2)):
    og_chunk_index, og_block_pos = world.pos_to_tile(rect.center)
    for yo in range(*range_y):
        for xo in range(*range_x):
            chunk_index, block_pos = world.correct_tile(og_chunk_index, og_block_pos, xo, yo)
            if block_pos in world.data[chunk_index]:
                block_rect = pygame.Rect(block_pos[0] * BS, block_pos[1] * BS, BS, BS)
                yield block_rect


def imgload(*path, scale=1, frames=1, convert=False, convert_alpha=True):
    img = pygame.image.load(Path(*path))
    if convert:
        img = img.convert()
    elif convert_alpha:
        img = img.convert_alpha()
    if frames == 1:
        return pygame.transform.scale_by(img, scale)
    else:
        imgs = []
        w, h = img.width / frames, img.height
        for x in range(frames):
            imgs.append(pygame.transform.scale_by(img.subsurface(x * w, 0, w, h), scale))
        return imgs



@dataclass
class Global:
    gravity: float = 0.14


glob = Global()
