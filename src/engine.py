from pathlib import Path
import pygame
from pygame.transform import scale, scale_by
from random import randint as rand
from random import uniform as randf
from random import choice
from math import sin, log as ln
from enum import Enum, IntFlag, auto
from dataclasses import dataclass
from math import floor, ceil, log10
import time


S = 3
BS = 10 * S


# CONTEXT MANAGERS
class Profile:
    def __enter__(self):
        self.last = time.perf_counter()
        return self
    
    def __exit__(self, e_type, e_val, trace):
        self.elapsed = sigfigs(time.perf_counter() - self.last, 3)


# FUNCTIONS
def sigfigs(x, n):
    if x == 0:
        return 0
    mag = floor(log10(abs(x)))
    scale = 10 ** (n - 1 - mag)
    return round(x * scale) / scale


def sign(n):
    if n > 0:
        return 1
    elif n < 0:
        return -1
    return 0


def cceil(n):
    if n == 0:
        return 0
    elif n > 0:
        return ceil(n)
    else:
        return floor(n)


def inflate_keep(rect, xo, yo=0):
    return rect.inflate(xo, yo).move(xo, yo)


def imgload(*path, scale=1, frames=None, convert=False, convert_alpha=True):
    img = pygame.image.load(Path(*path))
    if convert:
        img = img.convert()
    elif convert_alpha:
        img = img.convert_alpha()
    if frames is None:
        return pygame.transform.scale_by(img, scale)
    elif frames == 1:
        return [pygame.transform.scale_by(img, scale)]
    else:
        imgs = []
        w, h = img.width / frames, img.height
        for x in range(frames):
            imgs.append(pygame.transform.scale_by(img.subsurface(x * w, 0, w, h), scale))
        return imgs



# CLASSES
@dataclass
class Global:
    gravity: float = 0.14


class States(Enum):
    START = auto()
    PLAY = auto()


class Substates(Enum):
    PLAY = auto()
    MENU = auto()


glob = Global()
