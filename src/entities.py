from pyengine.ecs import *
from pyengine.pgbasics import *
from dataclasses import dataclass
from pathlib import Path
import pygame
from . import blocks


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


create_entity(
    Position((200, 200)),
    Image(blocks.images["soil_f"]),
)

@system(Position, Image)
class RenderSystem:
    def __init__(self, surf):
        self.surf = surf
        self.set_cache(True)
    
    def process(self):
        for pos, image in self.get_components():
            self.surf.blit(image.image, pos)
