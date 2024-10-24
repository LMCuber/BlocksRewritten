from pyengine.ecs import *
from pyengine.pgbasics import *
from dataclasses import dataclass
import pygame


@component
class Position(list):
    pass


@component
class Velocity(list):
    pass


@component
class Surface:
    def __init__(self, size, color):
        self.surf = pygame.Surface(size)
        self.surf.fill(color)


create_entity(Position((10, 10)), Surface((10, 10), BLACK))


@system(Position, Surface)
class RenderSystem:
    def __init__(self, surf):
        self.surf = surf
        self.set_cache(True)
    
    def process(self):
        for pos, surf in self.get_components():
            self.surf.blit(surf, pos)