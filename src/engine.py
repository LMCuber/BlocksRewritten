from pathlib import Path
import pygame
from pygame.transform import scale, scale_by
from random import randint as rand
from random import uniform as randf
from random import choice
from math import sin
from dataclasses import dataclass


S = 3
BS = 10 * S


def inflate_keep(rect, xo, yo=0):
    return rect.inflate(xo, yo).move(xo, yo)


def get_blocks_around(rect, world, scroll, range_x=(-2, 3), range_y=(-2, 3)):
    for yo in range(*range_x):
        for xo in range(*range_y):
            chunk_index, block_pos = world.pos_to_tile(rect.center, scroll)
            chunk_index, block_pos = world.correct_tile(chunk_index, block_pos, xo, yo)
            if world.data[chunk_index][block_pos] != "air":
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
