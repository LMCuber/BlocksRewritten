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
EMD = "—"

Pos = tuple[int, int]


# CONTEXT MANAGERS
class Profile:
    def __enter__(self):
        self.last = time.perf_counter()
        return self
    
    def __exit__(self, e_type, e_val, trace):
        self.elapsed = sigfigs(time.perf_counter() - self.last, 3)


# FUNCTIONS
def cyclic(l):
    return {l[i]: l[(i + 1) % len(l)] for i in range(len(l))} 


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
