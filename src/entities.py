from dataclasses import dataclass
from pathlib import Path
import pygame
from dataclasses import dataclass
from typing import Optional
from enum import Enum, IntFlag, auto
#
from pyengine.ecs import *
from pyengine.pgbasics import *
#
from . import blocks
from . import fonts
from .engine import *


del Window, Renderer, Texture, Image


# COMPONENTS -----------------------------------------------------
# enums of components (up here because the type hints otherwise do not compile)
class TransformFlags(IntFlag):
    PROJECTILE = auto()
    MOB = auto()


class DebugFlags(IntFlag):
    SHOW_CHUNK = auto()
    SHOW_HITBOX = auto()


class CollisionFlags(IntFlag):
    SEND = auto()
    RECV = auto()


# primitive components (int, float, str, etc.)
class MutInt:
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return f"MutInt({self.value})"
    
    def __iadd__(self, x):
        self.value += x
        return self
    
    def __isub__(self, x):
        self.value -= x
        return self


@component
class Health(MutInt): pass

@component
class TransformFlag(int): pass

@component
class DebugFlag(int): pass

@component
class CollisionFlag(int): pass


# dataclass components (structs without logical initialization)
@component
@dataclass
class Transform:
    pos: list[float, float]
    vel: list[float, float]
    flag: TransformFlag
    gravity: float
    acc: float = 0
    active: bool = True


@component
@dataclass
class PlayerFollower:
    ...


@dataclass
@component
class Rigidbody:
    bounce: float


# class components (classes with logical initialization)
@component
class Sprite:
    def __init__(self, path, num_frames, anim_speed, avel=0):
        self.images = imgload(path, scale=S, frames=num_frames)
        if not isinstance(self.images, list):
            self.images = [self.images]
        self.fimages = [pygame.transform.flip(image, True, False) for image in self.images]
        self.anim = 0
        self.anim_speed = anim_speed
        self.rect = self.images[0].get_frect()
        self.avel = avel
        self.rot = 0


# SYSTEMS -----------------------------------------------------
@system
class RenderSystem:
    def __init__(self, display):
        self.display = display
        self.set_cache(True)
        self.operates(Transform, Sprite)

    def process(self, scroll, world, chunks):
        for ent, chunk, (tr, sprite) in self.get_components(0, chunks=chunks):
            if tr.active:
                # physics
                tr.vel[1] += tr.gravity
                tr.pos[1] += tr.vel[1]
                sprite.rect.topleft = tr.pos

                x_disp = ceil(abs(tr.vel[0] / BS))
                range_x = (-x_disp, x_disp + 1)
                y_disp = ceil(abs(tr.vel[1] / BS))
                range_y = (-y_disp, y_disp + 1)
                for rect in get_blocks_around(sprite.rect, world, range_x=range_x, range_y=range_y):
                    pygame.draw.rect(self.display, pygame.Color("orange"), (rect.x - scroll[0], rect.y - scroll[1], *rect.size), 1)
                    if sprite.rect.colliderect(rect):
                        if tr.vel[1] > 0:
                            tr.pos[1] = rect.top - sprite.rect.height
                        else:
                            tr.pos[1] = rect.bottom
                        # stop projectiles when hitting the ground
                        if tr.flag & TransformFlags.PROJECTILE:
                            tr.active = False
                        tr.vel[1] = 0
                        sprite.rect.topleft = tr.pos
                
                # Euler's method for movement
                tr.vel[0] += tr.acc
                tr.pos[0] += tr.vel[0]
                sprite.rect.topleft = tr.pos

                for rect in get_blocks_around(sprite.rect, world, range_x=range_x, range_y=range_y):
                    pygame.draw.rect(self.display, pygame.Color("cyan"), (rect.x - scroll[0], rect.y - scroll[1], *rect.size), 1)
                    if sprite.rect.colliderect(rect):
                        if tr.vel[0] > 0:
                            tr.pos[0] = rect.left - sprite.rect.width
                        else:
                            tr.pos[0] = rect.right
                        # stop the horizontal movement if projectile hits a wall
                        if tr.flag & TransformFlags.PROJECTILE:
                            tr.vel[0] = 0
                        sprite.rect.topleft = tr.pos
                
                # jump over obstacles if it is a mob
                if tr.flag & TransformFlags.MOB:
                    extended_rect = inflate_keep(sprite.rect, 20 * sign(tr.vel[0]))
                    # pygame.draw.rect(self.display, (120, 120, 120), (extended_rect.x - scroll[0], extended_rect.y - scroll[1], *extended_rect.size), 1)
                    for rect in get_blocks_around(extended_rect, world):
                        if extended_rect.colliderect(rect):
                            tr.vel[1] = -3

            # animate and render
            sprite.anim += sprite.anim_speed
            try:
                sprite.images[int(sprite.anim)]
            except IndexError:
                sprite.anim = 0
            finally:
                # calc. position of rendering
                blit_pos = (tr.pos[0] - scroll[0], tr.pos[1] - scroll[1])
                # rotate sprite
                sprite.rot += sprite.avel
                img = (sprite.images if tr.vel[0] > 0 else sprite.fimages)[int(sprite.anim)]
                # render sprite
                self.display.blit(img, blit_pos)


@system
class PlayerFollowerSystem:
    def __init__(self, display):
        self.display = display
        self.set_cache(True)
        self.operates(PlayerFollower, Transform, Sprite)
    
    def process(self, player, chunks):
        for ent, chunk, (pf, tr, sprite) in self.get_components(0, chunks=chunks):
            if tr.pos[0] + sprite.rect.width / 2 > player.rect.centerx and tr.vel[0] > 0:
                tr.vel[0] *= -1
            elif tr.pos[0] + sprite.rect.width / 2 < player.rect.centerx and tr.vel[0] < 0:
                tr.vel[0] *= -1


@system
class DebugSystem:
    def __init__(self, display):
        self.display = display
        self.set_cache(True)
        self.operates(DebugFlag, Transform, Health)
    
    def process(self, scroll, chunks):
        for ent, chunk, (flags, tr, health) in self.get_components(0, chunks=chunks):
            blit_pos = (tr.pos[0] - scroll[0], tr.pos[1] - scroll[1])
            if flags & DebugFlags.SHOW_CHUNK:
                write(self.display, "center", chunk, fonts.orbitron[20], BROWN, blit_pos[0], blit_pos[1] - 20)


@system
class CollisionSystem:
    def __init__(self):
        self.set_cache(True)
        self.operates(CollisionFlag, Transform, Sprite)
        self.operates(CollisionFlag, Transform, Sprite, Health)
    
    def process(self, chunks):
        """
        O(n^2) collision detection, I don't think I'll need a quadtree for this
        since I already use a chunk system which spatially divides the entities
        """
        # check the damage inflicters
        for ent, chunk, (col_flag, tr, sprite) in self.get_components(0, chunks=chunks):
            if col_flag & CollisionFlags.SEND:
                rect = pygame.Rect(tr.pos, sprite.rect.size)
                # check for damage receivers
                for ent2, chunk2, (col_flag2, tr2, sprite2, health2) in self.get_components(1, chunks=chunks):
                    if col_flag2 & CollisionFlags.RECV:
                        rect2 = pygame.Rect(tr2.pos, sprite2.rect.size)
                        if rect.colliderect(rect2):
                            sprite2.images = sprite2.fimages = [pygame.Surface((30, 30))]


@system
class DisplayHealthSystem:
    def __init__(self, display):
        self.display = display
        self.set_cache(True)
        self.operates(Health, Transform, Sprite)
    
    def process(self, scroll, chunks):
        for ent, chunk, (health, tr, sprite) in self.get_components(0, chunks=chunks):
            blit_pos = (tr.pos[0] - scroll[0], tr.pos[1] - scroll[1])
            write(self.display, "center", health, fonts.orbitron[20], BROWN, blit_pos[0], blit_pos[1] - 40)
