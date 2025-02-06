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
    INACTIVE = auto()
    

# primitive components (int, float, str, etc.)
class MutInt:
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return f"MutInt({str(bin(self.value)).removeprefix("0b")})"
    
    def __iadd__(self, x):
        self.value += x
        return self
    
    def __isub__(self, x):
        self.value -= x
        return self
    
<<<<<<< HEAD
    def __and__(self, other):
        return self.value & other
    
    def __rand__(self, other):
        return self.value & other
    
    def set(self, n):  # n is a Flag, so bit_length() - 1 returns the number of bits (16 -> 4 because 2**4 == 16)
        self.value |= (1 << (n.bit_length() - 1))

=======
    def __imul__(self, x):
        self.value *= x
        return self
    
    def __idiv__(self, x):
        self.value /= x
        return self
>>>>>>> 34c1414115d292aaf1e3551de526768d0d2a6a7a

@component
class TransformFlag(int): pass

@component
class DebugFlag(int): pass

@component
class CollisionFlag(MutInt): pass


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


@component
class Health:
    def __init__(self, value):
        self.value = self.trail = self.max = value

    def __isub__(self, n):
        self.value -= n
        return self


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
        self.xo = self.rect.width / 2
        self.yo = self.rect.height / 2
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

                x_disp = ceil(abs(tr.vel[0] / BS)) + ceil(sprite.xo / BS)
                range_x = (-x_disp, x_disp + 1)
<<<<<<< HEAD
                y_disp = ceil(abs(tr.vel[1] / BS)) + ceil(sprite.yo / BS)
                range_y = (-y_disp, y_disp + 1)
                
                for rect in world.get_blocks_around(sprite.rect, range_x=range_x, range_y=range_y):
=======
                y_disp = ceil(abs(tr.vel[1] / BS))
                range_y = (-y_disp, y_disp + 1 + 3)

                for rect in get_blocks_around(sprite.rect, world, range_x=range_x, range_y=range_y):
>>>>>>> 34c1414115d292aaf1e3551de526768d0d2a6a7a
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

                for rect in world.get_blocks_around(sprite.rect, range_x=range_x, range_y=range_y):
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
                    for rect in world.get_blocks_around(extended_rect):
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
            
            pygame.draw.rect(self.display, (0, 255, 0), (sprite.rect.x - scroll[0], sprite.rect.y - scroll[1], *sprite.rect.size), 1)


@system
class PlayerFollowerSystem:
    def __init__(self, display):
        self.display = display
        self.set_cache(True)
        self.operates(PlayerFollower, Transform, Sprite)
    
    def process(self, player, chunks):
        for ent, chunk, (pf, tr, sprite) in self.get_components(0, chunks=chunks):
            if tr.pos[0] + sprite.xo > player.rect.centerx and tr.vel[0] > 0:
                tr.vel[0] *= -1
            elif tr.pos[0] + sprite.xo < player.rect.centerx and tr.vel[0] < 0:
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
        for s_ent, s_chunk, (s_col_flag, s_tr, s_sprite) in self.get_components(0, chunks=chunks):
            if s_tr.active and s_col_flag & CollisionFlags.SEND:
                s_rect = pygame.Rect(s_tr.pos, s_sprite.rect.size)
                # check for damage receivers
                for r_ent, r_chunk, (r_col_flag, r_tr, r_sprite, r_health) in self.get_components(1, chunks=chunks):
                    if r_col_flag & CollisionFlags.RECV and not (s_col_flag & CollisionFlags.INACTIVE):
                        # HIT!!!
                        r_rect = pygame.Rect(r_tr.pos, r_sprite.rect.size)
                        if s_rect.colliderect(r_rect):
                            r_health -= rand(4, 14)
                            # check if the receiver is dead
                            if r_health.value <= 0:
                                r_sprite.images = r_sprite.fimages = [pygame.Surface((30, 30))]
                            # make the bullet inactive
                            s_col_flag.set(CollisionFlags.INACTIVE)


@system
class DisplayHealthSystem:
    def __init__(self, display):
        self.display = display
        self.set_cache(True)
        self.operates(Health, Transform, Sprite)
    
    def process(self, scroll, chunks):
        for _, _, (health, tr, sprite) in self.get_components(0, chunks=chunks):
            if 0 < health.value < health.max:
                # process the animation
                health.trail -= (health.trail - health.value) * 0.03
                # display the health bar
                bg_rect = pygame.Rect(0, 0, 70, 10)
                bg_rect.midtop = (tr.pos[0] + sprite.xo - scroll[0], tr.pos[1] - 20 - scroll[1])
                pygame.draw.rect(self.display, BLACK, bg_rect)
                hl_rect = bg_rect.inflate(-4, -4)
                hl_rect.width *= health.value / health.max
                tr_rect = bg_rect.inflate(-4, -4)
                tr_rect.width *= health.trail / health.max
                pygame.draw.rect(self.display, PINK, tr_rect)
                pygame.draw.rect(self.display, RED, hl_rect)
