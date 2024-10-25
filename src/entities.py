from dataclasses import dataclass
from pathlib import Path
import pygame
#
from pyengine.ecs import *
from pyengine.pgbasics import *
#
from . import blocks
from .engine import *



del Image


@component
class Position(list):
    pass


@component
class Velocity(list):
    pass


@component
class Image:
    def __init__(self, image):
        self.image = image


for y in range(10):
    for x in range(100):
        create_entity(
            Position((x * BS + rand(-10, 10) + 100, y * BS + rand(-10, 10) + 100)),
            Image(choice(list(blocks.images.values()))),
        )


@system(Position, Image)
class RenderSystem:
    def __init__(self, surf):
        self.surf = surf
        self.set_cache(True)
    
    def process(self):
        return
        for pos, image in self.get_components():
            self.surf.blit(image.image, pos)
