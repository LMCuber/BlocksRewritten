from dataclasses import dataclass
from pathlib import Path
import pygame
from dataclasses import dataclass
import yaml
#
from pyengine.ecs import *
from pyengine.pgbasics import *
#
from . import blocks
from . import fonts
from .engine import *


del Window, Renderer, Texture, Image


# anim data masterclass (hehe)
class AnimData:
    with open(Path("res", "data", "player_animations.yaml")) as f:
        yaml_data = yaml.safe_load(f);

    data = {}
    for skin in yaml_data:
        data[skin] = {}
        for mode in yaml_data[skin]:
            data[skin][mode] = {}
            data[skin][mode]["images"] = imgload("res", "images", "player_animations", skin, f"{mode}.png", scale=S, frames=yaml_data[skin][mode]["frames"])
            data[skin][mode]["offset"] = yaml_data[skin][mode].get("offset", 0)
            data[skin][mode]["speed"] = yaml_data[skin][mode].get("speed", 0.08)
            data[skin][mode]["hitbox"] = yaml_data[skin][mode].get("hitbox", (1, 1))

    @classmethod
    def get(cls, skin, mode):
        if skin == "_default":
            mode = "_default_" + mode
        return [cls.data[skin][mode][attr] for attr in ["images", "offset", "speed", "hitbox"]]
    

# COMPONENTS -----------------------------------------------------
# enums of components (up here because the type hints otherwise do not compile)
# DO NOT INSTANTIATE, THEY ARE MEANT TO BE WRAPPED INSIDE THE CORRESPONDING CLASSES, e.g. CollisionFlag(CollisionFlags.SEND | CollisionFlags.INACTIVE) or something ;)
class TransformFlags(IntFlag):
    PROJECTILE = auto()
    MOB = auto()
    NONE = auto()


class DebugFlags(IntFlag):
    SHOW_CHUNK = auto()
    SHOW_HITBOX = auto()


class CollisionFlags(IntFlag):
    SEND = auto()
    RECV = auto()
    INACTIVE = auto()


# primitive components (int, float, str, etc.) (bool can't exist since only the True and False singletons can be bool)
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
    
    def __and__(self, other):
        return self.value & other
    
    def __rand__(self, other):
        return self.value & other
    
    def set(self, n):  # n is a Flag, so bit_length() - 1 returns the number of bits (16 -> 4 because 2**4 == 16)
        self.value |= (1 << (n.bit_length() - 1))

    def __imul__(self, x):
        self.value *= x
        return self
    
    def __idiv__(self, x):
        self.value /= x
        return self


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
    flag: TransformFlag = TransformFlag(TransformFlags.NONE)
    gravity: float = 0
    acc: float = 0
    active: bool = True
    sine: tuple[float, float] = (0, 0)

    def __post_init__(self):
        if any(self.sine):
            self.sine_offset = randf(0, 2 * pi)


@component
@dataclass
class PlayerFollower:
    ...


@component
@dataclass
class Rigidbody:
    bounce: float
    

@component
class Health:
    def __init__(self, value):
        self.value = self.trail = self.max = value

    def __isub__(self, n):
        self.value -= n
        return self


@component
@dataclass
class Drop:
    block: str


# class components (classes with logical initialization)
@component
class Sprite:
    """
    If a sprite gets passed a single image, then it needs no offsetting per animation frame, since it is a still image.
    But animation sprites need to dynamically poll [images and offsets] from AnimData.get() 
    """
    @classmethod
    def from_img(cls, img):
        self = cls()
        self.images = [img]
        self.fimages = [pygame.transform.flip(image, True, False) for image in self.images]
        self.anim = 0
        self.anim_speed = 0
        self.rect = self.images[0].get_frect()
        self.avel = 0
        self.rot = 0
        return self

    @classmethod
    def from_path(cls, path, pos, anchor="midbottom"):
        self = cls()
        self.anim = 0
        self.anim_skin = path.parts[-2]  # "nutcracker"
        self.anim_mode = path.stem  # "run"
        # -- BELOW UPDATED EVERY FRAME --
        self.images = []
        self.offset = (0, 0)
        self.anim_speed = 0.2
        self.anchor = anchor
        # hitbox fetch data and hitbox itself
        self.pos = pos
        self.hitbox_size = None
        self.hitbox = None
        return self


@component
class Hitbox(pygame.Rect):
    def __init__(self, *args, anchor=None):
        super().__init__(*args)
        if anchor is not None:
            setattr(self, anchor, self.topleft)


@component
class DamageText:
    def __init__(self, damage: float,  max_y: int, size: int = 20, color: tuple = BLACK):
        self.max_y = max_y
        self.img = fonts.orbitron[size].render(str(damage), True, color)
        self.inited = False
        self.offset = None
    

# SYSTEMS -----------------------------------------------------
@system
class PhysicsSystem:
    def __init__(self):
        self.set_cache(True)
        self.operates(Transform, Sprite)
    
    def process(self, world, hitboxes: bool, chunks):
        for ent, chunk, (tr, sprite) in self.get_components(0, chunks=chunks):
            # initialize hitbox if it doesn't exist yet
            if sprite.hitbox is None:
                sprite.hitbox = pygame.Rect(0, 0, *sprite.hitbox_size)
                setattr(sprite.hitbox, sprite.anchor, sprite.pos)

            # hitbox reference
            hitbox = sprite.hitbox

            # physics
            x_disp = ceil(abs(tr.vel[0] / BS)) + ceil(hitbox.width / 2 / BS)
            range_x = (-x_disp, x_disp + 1)
            y_disp = ceil(abs(tr.vel[1] / BS)) + ceil(hitbox.height / 2 / BS)
            range_y = (-y_disp, y_disp + 3)

            for rect in world.get_blocks_around(hitbox, range_x=range_x, range_y=range_y):
                if hitbox.colliderect(rect):
                    if tr.vel[1] > 0:
                        hitbox.bottom = rect.top
                    else:
                        hitbox.top = rect.bottom
                    # stop projectiles when hitting the ground
                    if tr.flag & TransformFlags.PROJECTILE:
                        tr.active = False
                    tr.vel[1] = 0
            
            for rect in world.get_blocks_around(hitbox, range_x=range_x, range_y=range_y):
                if hitbox.colliderect(rect):
                    if tr.vel[0] > 0:
                        hitbox.right = rect.left
                    else:
                        hitbox.left = rect.right
                    # stop the horizontal movement if projectile hits a wall
                    if tr.flag & TransformFlags.PROJECTILE:
                        tr.vel[0] = 0
            
            # jump over obstacles if it is a mob
            return
            if tr.flag & TransformFlags.MOB:
                extended_rect = inflate_keep(sprite.rect, 20 * sign(tr.vel[0]))
                # pygame.draw.rect(self.display, (120, 120, 120), (extended_rect.x - scroll[0], extended_rect.y - scroll[1], *extended_rect.size), 1)
                for rect in world.get_blocks_around(extended_rect):
                    if extended_rect.colliderect(rect):
                        tr.vel[1] = -3


@system
class AnimationSystem:
    def __init__(self):
        self.set_cache(True)
        self.operates(Sprite)
    
    def process(self, chunks):
        for ent, chunk, (sprite,) in self.get_components(0, chunks=chunks):
            # get the spritesheet images, offset and speed
            sprite.images, sprite.offset, sprite.anim_speed, sprite.hitbox_size = AnimData.get(sprite.anim_skin, sprite.anim_mode)
            # increase the animation frame
            sprite.anim += sprite.anim_speed
            try:
                sprite.images[int(sprite.anim)]
            except IndexError:
                sprite.anim = 0


@system
class RenderSystem:
    def __init__(self, display):
        self.display = display
        self.set_cache(True)
        self.operates(Sprite, Transform)
    
    def process(self, scroll, chunks):
        for ent, chunk, (sprite, tr) in self.get_components(0, chunks=chunks):
            # hitbox def
            hitbox = sprite.hitbox
            # get which image
            image = sprite.images[int(sprite.anim)]
            # flip the image if player is moving to the left instead of to the right
            if tr.vel[0] < 0:
                image = pygame.transform.flip(image, True, False)
            # render the player
            scrolled_hitbox = hitbox.move(-scroll[0], -scroll[1])
            blit_rect = image.get_rect(center=scrolled_hitbox.center).move(0, sprite.offset)

            # debugging
            pygame.draw.rect(self.display, GREEN, blit_rect, 1)
            pygame.draw.rect(self.display, ORANGE, scrolled_hitbox, 1)

            self.display.blit(image, blit_rect)


@system
class DeprRenderSystem:
    def __init__(self, display):
        self.display = display
        self.set_cache(True)
        self.operates(Transform, Sprite)

    def process(self, scroll, world, hitboxes, chunks):
        for ent, chunk, (tr, sprite) in self.get_components(0, chunks=chunks):
            if tr.active:
                # physics
                tr.vel[1] += tr.gravity
                tr.pos[1] += tr.vel[1]
                sprite.rect.topleft = tr.pos

                x_disp = ceil(abs(tr.vel[0] / BS)) + ceil(sprite.xo / BS)
                range_x = (-x_disp, x_disp + 1)
                y_disp = ceil(abs(tr.vel[1] / BS)) + ceil(sprite.yo / BS)
                range_y = (-y_disp, y_disp + 3)
                
                for rect in world.get_blocks_around(sprite.rect, range_x=range_x, range_y=range_y):
                    if hitboxes:
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
                    if hitboxes:
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
                if tr.flag & TransformFlags.MOB and False:
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
                blit_pos = [tr.pos[0] - scroll[0], tr.pos[1] - scroll[1]]
                # rotate sprite
                sprite.rot += sprite.avel
                img = (sprite.images if tr.vel[0] >= 0 else sprite.fimages)[int(sprite.anim)]
                # add sine to the sprite if necessary
                if any(tr.sine):
                    blit_pos[1] += sin(ticks() * 2 * pi / 1000 * tr.sine[0] + tr.sine_offset) * tr.sine[1]
                # render sprite
                self.display.blit(img, blit_pos)
            
            if hitboxes:
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
        self.operates(CollisionFlag, Transform, Sprite)  # regular collisions and senders
        self.operates(CollisionFlag, Transform, Sprite, Health)  # collisions of receivers
    
    def process(self, player, chunks):
        """
        O(n^2) collision detection, I don't think I'll need a quadtree for this
        since I already use a chunk system which is efficient enough
        """
        # check the damage inflicters
        for ent, chunk, (col_flag, tr, sprite) in self.get_components(0, chunks=chunks):
            s_ent, s_chunk, s_col_flag, s_tr, s_sprite = ent, chunk, col_flag, tr, sprite
            rect = pygame.Rect(s_tr.pos, s_sprite.rect.size)
            s_rect = rect
            #
            if s_tr.active and s_col_flag & CollisionFlags.SEND:
                # check for damage receivers
                for r_ent, r_chunk, (r_col_flag, r_tr, r_sprite, r_health) in self.get_components(1, chunks=chunks):
                    if r_col_flag & CollisionFlags.RECV and not (s_col_flag & CollisionFlags.INACTIVE):
                        # HIT!!!
                        r_rect = pygame.Rect(r_tr.pos, r_sprite.rect.size)
                        if s_rect.colliderect(r_rect):
                            r_health -= 20
                            # damage number as text
                            create_entity(
                                Transform([*r_rect.center], [0, -0.5], gravity=0.01),
                                DamageText(rand(5, 20), r_rect.centery - 100),
                                chunk=0
                            )
                            # check if the receiver is dead, if so, kill it
                            if r_health.value <= 0:
                                self.delete(1, r_ent, r_chunk)
                            # make the bullet inactive
                            s_col_flag.set(CollisionFlags.INACTIVE)


@system
class DamageTextSystem:
    def __init__(self, display):
        self.display = display
        self.set_cache(True)
        self.operates(Transform, DamageText)
    
    def process(self, scroll, chunks):
        for ent, chunk, (tr, dam) in self.get_components(0, chunks=chunks):
            # init the offset
            if not dam.inited:
                dam.offset = tr.pos[1] - dam.max_y
                dam.inited = True
            # move the text up
            tr.pos[1] += (dam.max_y - tr.pos[1]) * 0.01
            # apply translusence and destroy when needed
            dam.img.set_alpha(((tr.pos[1] - dam.max_y) / dam.offset) * 255)
            if dam.img.get_alpha() <= 10:
                self.delete(0, ent, chunk)
            # render the font
            blit_pos = [tr.pos[0] - scroll[0], tr.pos[1] - scroll[1]]
            self.display.blit(dam.img, blit_pos)


@system
class DropSystem:
    def __init__(self, display):
        self.display = display
        self.set_cache(True)
        self.operates(Drop, Transform, Sprite)
    
    def process(self, player, scroll, chunks):
        for ent, chunk, (drop, tr, sprite) in self.get_components(0, chunks=chunks):
            rect = pygame.Rect(tr.pos, sprite.rect.size)
            if rect.colliderect(player.rect):
                player.inventory.add(drop.block, 1)
                self.delete(0, ent, chunk)


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
                health.trail -= (health.trail - health.value) * 0.02
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
