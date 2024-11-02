from dataclasses import dataclass
from pathlib import Path
import pygame
from dataclasses import dataclass
#
from pyengine.ecs import *
from pyengine.pgbasics import *
#
from . import blocks
from .engine import *



del Window, Renderer, Texture, Image


@component
@dataclass
class Transform:
    pos: list[float, float]
    vel: list[float, float]
    gravity: float


@component
class Sprite:
    def __init__(self, path, num_frames, anim_speed):
        self.images = imgload(path, scale=S, frames=num_frames)
        self.fimages = [pygame.transform.flip(image, True, False) for image in self.images]
        self.anim = 0
        self.anim_speed = anim_speed
        self.rect = self.images[0].get_frect()


@component
class FollowsPlayer:
    pass


for _ in range(1):
    create_entity(
        Transform([-100, -400], [randf(0.5, 1), 0.0], glob.gravity),
        Sprite(Path("res", "images", "mobs", "penguin", "walk.png"), 4, 0.1),
        FollowsPlayer(),
    )


@system(Transform, Sprite)
class RenderSystem:
    def __init__(self, display):
        self.display = display
        self.set_cache(True)

    def process(self, scroll, world):
        for tr, sprite in self.get_components():
            # physics
            tr.vel[1] += tr.gravity
            tr.pos[1] += tr.vel[1]
            sprite.rect.topleft = tr.pos

            # pygame.draw.rect(self.display, (120, 120, 120), (sprite.rect.x - scroll[0], sprite.rect.y - scroll[1], *sprite.rect.size), 1)
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
                    tr.vel[1] = 0
                    sprite.rect.topleft = tr.pos
            
            tr.pos[0] += tr.vel[0]
            sprite.rect.topleft = tr.pos

            for rect in get_blocks_around(sprite.rect, world):
                if sprite.rect.colliderect(rect):
                    if tr.vel[0] > 0:
                        tr.pos[0] = rect.left - sprite.rect.width
                    else:
                        tr.pos[0] = rect.right
                    sprite.rect.topleft = tr.pos
            
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
                blit_pos = (tr.pos[0] - scroll[0], tr.pos[1] - scroll[1])
                self.display.blit((sprite.images if tr.vel[0] > 0 else sprite.fimages)[int(sprite.anim)], blit_pos)


@system(FollowsPlayer, Transform, Sprite)
class PlayerFollowerSystem:
    def __init__(self, display):
        self.display = display
        self.set_cache(True)
    
    def process(self, player):
        for _, tr, sprite in self.get_components():
            if tr.pos[0] + sprite.rect.width / 2 > player.rect.centerx and tr.vel[0] > 0:
                tr.vel[0] *= -1
            elif tr.pos[0] + sprite.rect.width / 2 < player.rect.centerx and tr.vel[0] < 0:
                tr.vel[0] *= -1