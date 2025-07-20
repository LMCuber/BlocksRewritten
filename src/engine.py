from pathlib import Path
import pygame
from pygame.transform import scale, scale_by
from random import randint as rand
from random import uniform as randf
from random import choice
from enum import Enum, IntFlag, auto
from dataclasses import dataclass
from math import sin, floor, ceil, log10, sqrt
from math import log as ln
import time
from colorama import Fore
import colorama
from contextlib import suppress
#
import pyengine.pgbasics as pgb
#


colorama.init(autoreset=True)


CW = 16
CH = 16
S = 3
BS = 10 * S

Pos = tuple[int, int]


# CONTEXT MANAGERS
class Profile:
    def __enter__(self):
        self.last = time.perf_counter()
        return self
    
    def __exit__(self, e_type, e_val, trace):
        self.elapsed = sigfigs(time.perf_counter() - self.last, 3)


# FUNCTIONS
def clamp(n, min_, max_):
    return min(max(n, min_), max_)


def sigfigs(x, n):
    if x == 0:
        return 0
    mag = floor(log10(abs(x)))
    scale = 10 ** (n - 1 - mag)
    return round(x * scale) / scale


def cceil(n):
    if n == 0:
        return 0
    elif n > 0:
        return ceil(n)
    else:
        return floor(n)


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
