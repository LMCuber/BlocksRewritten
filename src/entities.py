from dataclasses import dataclass
from pathlib import Path
import pygame
from dataclasses import dataclass
import yaml
#
from pyengine.ecs import *
from pyengine.pgbasics import *
#
from . import fonts
from .engine import *


del Window, Renderer, Texture, Image


# anim data masterclass (hehe)
class AnimData:
    data = {}
    for entity_type in ["player_animations", "mobs", "statics"]:
        with open(Path("res", "data", f"{entity_type}.yaml")) as f:
            yaml_data = yaml.safe_load(f);

        for skin in yaml_data:
            # load the defaults (different from _default, which is the default player character)
            if skin == "DEFAULT":
                default_speed = yaml_data[skin]["speed"]
                continue

            data[skin] = {}
            for mode in yaml_data[skin]:
                data[skin][mode] = {}
                data[skin][mode]["images"] = imgload("res", "images", entity_type, skin, f"{mode}.png", scale=S, frames=yaml_data[skin][mode]["frames"])
                data[skin][mode]["offset"] = yaml_data[skin][mode].get("offset", 0)
                data[skin][mode]["speed"] = yaml_data[skin][mode].get("speed", default_speed)
                data[skin][mode]["hitbox"] = yaml_data[skin][mode].get("hitbox", None)
        
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
        self.last_tile = None
        self.last_blocks_around = None
        if any(self.sine):
            self.sine_offset = randf(0, 2 * pi)


@component
@dataclass
class PlayerFollower:
    max_distance: int
    follow_delay: int = 500

    def __post_init__(self):
        self.last_followed: int = 0
        self.started_following: bool = False


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
    @classmethod
    def from_img(cls, img):
        self = cls()
        self.hitbox_size = None
        self.offset = 0

        self.images = [img]
        self.fimages = [pygame.transform.flip(image, True, False) for image in self.images]
        self.anim = 0
        self.anim_skin = None
        self.anim_speed = 0
        self.rect = self.images[0].get_frect()
        self.avel = 0
        self.rot = 0
        return self

    @classmethod
    def from_path(cls, path):
        self = cls()
        self.anim = 0
        self.rot = 0
        self.anim_skin = path.parts[-2]  # "nutcracker"
        self.anim_mode = path.stem  # "run"
        # -- BELOW UPDATED EVERY FRAME --
        self.images = []
        self.offset = 0
        self.anim_speed = 0.2
        return self


@component
@dataclass
class Animation:
    pass


@component
class Hitbox(pygame.FRect):
    def __init__(self, *args, anchor=None):
        super().__init__(*args)
        self.anchor = anchor
        if anchor is not None:
            setattr(self, anchor, self.topleft)


@component
class DamageText:
    def __init__(self, damage: float,  max_y: int, size: int = 20, color: tuple = BLACK):
        self.max_y = max_y
        self.img = fonts.orbitron[size].render(str(damage), True, color)
        self.inited = False
        self.offset = None


@component
@dataclass
class Headbutter:
    force: int = 10
    

# SYSTEMS -----------------------------------------------------
@system(cache=True)
class PhysicsSystem:
    def __init__(self, display):
        self.display = display
        self.set_cache(True)
        self.operates(Transform, Hitbox, Sprite)
    
    def process(self, world, scroll, collisions: bool, chunks):
        for ent, chunk, (tr, hitbox, sprite) in self.get_components(0, chunks=chunks):
            sprite.rot = 0

            # check if hitbox needs to be initialized by a Sprite
            # physics
            if hitbox.size == (0, 0):
                if sprite.hitbox_size is None:
                    hitbox.size = sprite.images[0].size
                else:
                    hitbox.size = sprite.hitbox_size

            x_disp = ceil(abs(tr.vel[0] / BS)) + ceil(hitbox.width / 2 / BS)
            range_x = (-x_disp, x_disp)
            y_disp = ceil(abs(tr.vel[1] / BS)) + ceil(hitbox.height / 2 / BS)
            range_y = (-y_disp, y_disp)

            # vertical movement
            tr.vel[1] += tr.gravity
            hitbox.y += tr.vel[1]

            # get the cached neighboring blocks if on same block as last frame
            current_tile = world.pos_to_tile(hitbox.center)
            if tr.last_tile is None:
                # first iteration, so no cache yet
                tr.last_blocks_around = world.get_blocks_around(hitbox, range_x=range_x, range_y=range_y)
            else:
                # has cache, so check whether current position is same as last position
                if current_tile != tr.last_tile:
                    tr.last_blocks_around = world.get_blocks_around(hitbox, range_x=range_x, range_y=range_y)
            tr.last_tile = current_tile

            # access cached collision blocks
            for rect in tr.last_blocks_around:
                if collisions:
                    pygame.draw.rect(self.display, ORANGE, rect.move(-scroll[0], -scroll[1]), 1)
                if hitbox.colliderect(rect):
                    if tr.vel[1] > 0:
                        hitbox.bottom = rect.top
                    else:
                        hitbox.top = rect.bottom
                    # stop projectiles when hitting the ground
                    if tr.flag & TransformFlags.PROJECTILE:
                        tr.active = False
                    tr.vel[1] = 0
            
            # horizontal movement
            hitbox.x += tr.vel[0]

            # access cached collision blocks
            for rect in tr.last_blocks_around:
                if hitbox.colliderect(rect):
                    if tr.vel[0] > 0:
                        hitbox.right = rect.left
                    else:
                        hitbox.left = rect.right
                    # stop the horizontal movement if projectile hits a wall
                    if tr.flag & TransformFlags.PROJECTILE:
                        tr.vel[0] = 0
            
            # jump over obstacles if it is a mob
            if tr.flag & TransformFlags.MOB:
                # extended displacement range for jumping because rectangle is more in front
                x_disp_ext = ceil(abs(tr.vel[0] / BS)) + ceil(hitbox.width / 2 / BS)
                range_x_ext = (-x_disp_ext, x_disp_ext)
                y_disp_ext = ceil(abs(tr.vel[1] / BS)) + ceil(hitbox.height / 2 / BS)
                range_y_ext = (-y_disp_ext, y_disp_ext)

                o = 20
                extended_rect = hitbox.inflate(o * 2, 0).move(o * sign(tr.vel[0]), 0)
                if hitboxes:
                    pygame.draw.rect(self.display, (120, 120, 120), extended_rect.move(-scroll[0], -scroll[1]), 1)
                for rect in world.get_blocks_around(extended_rect, range_x=range_x_ext, range_y=range_y_ext):
                    # draw the hitboxes
                    if hitboxes:
                        pygame.draw.rect(self.display, GREEN, rect.move(-scroll[0], -scroll[1]), 1)
                    # jump the mob because it sees a block in front of it
                    if extended_rect.colliderect(rect):
                        tr.vel[1] = -2
                        sprite.rot = 90


@system(cache=True)
class AnimationSystem:
    def __init__(self):
        self.set_cache(True)
        self.operates(Animation, Sprite)
    
    def process(self, chunks):
        for ent, chunk, (anim, sprite) in self.get_components(0, chunks=chunks):
            # safe
            if sprite.anim_skin is None:
                return

            # get the spritesheet images, offset and speed
            sprite.images, sprite.offset, sprite.anim_speed, sprite.hitbox_size = AnimData.get(sprite.anim_skin, sprite.anim_mode)
            # increase the animation frame
            sprite.anim += sprite.anim_speed
            try:
                sprite.images[int(sprite.anim)]
            except IndexError:
                sprite.anim = 0


@system(cache=True)
class ChunkRepositioningSystem:
    def __init__(self):
        self.set_cache(True)
        self.operates(Hitbox)
    
    def process(self, chunks):
        return
        for ent, chunk, arch, (hitbox,) in self.get_components(0, chunks=chunks, archetype=True):
            # don't try to move to adjacent chunk if chunk is None (unbound)
            if chunk is None:
                continue

            # the percentage is: (block position - chunk block position) / chunk size
            x, y = hitbox.center
            perc_x = ((x / BS) - (chunk[0] * CW)) / CW
            perc_y = ((y / BS) - (chunk[1] * CH)) / CH
            # check if out of bounds and relocate
            if perc_x < 0:
                self.relocate(chunk, arch, ent, (chunk[0] - 1, chunk[1]))
            elif perc_x >= 1:
                self.relocate(chunk, arch, ent, (chunk[0] + 1, chunk[1]))
            elif perc_y < 0:
                self.relocate(chunk, arch, ent, (chunk[0], chunk[1] - 1))
            elif perc_y >= 1:
                self.relocate(chunk, arch, ent, (chunk[0], chunk[1] + 1))


@system(cache=True)
class RenderSystem:
    def __init__(self, display):
        self.display = display
        self.set_cache(True)
        self.operates(Transform, Hitbox, Sprite)
    
    def process(self, scroll, hitboxes, chunks):
        num = 0
        for ent, chunk, (tr, hitbox, sprite) in self.get_components(0, chunks=chunks):
            num += 1
            # get which image
            image = sprite.images[int(sprite.anim)]
            # rotate it when needed
            if sprite.rot:  # (!= 0)
                image = pygame.transform.rotate(image, sprite.rot)
            # flip the image if player is moving to the left instead of to the right
            if tr.vel[0] < 0:
                image = pygame.transform.flip(image, True, False)
            # render the player
            scrolled_hitbox = hitbox.move(-scroll[0], -scroll[1])
            blit_rect = image.get_rect(center=scrolled_hitbox.center).move(0, sprite.offset)

            # if chunk is not None:
            #     write(self.display, "center", chunk, fonts.orbitron[20], BLACK, scrolled_hitbox.centerx, scrolled_hitbox.centery - 80)

            self.display.blit(image, blit_rect)
            
            # debugging
            if hitboxes:
                pygame.draw.rect(self.display, GREEN, blit_rect, 1)
                pygame.draw.rect(self.display, ORANGE, scrolled_hitbox, 1)
        
        return num


@system(cache=True)
class PlayerFollowerSystem:
    def __init__(self, display):
        self.display = display
        self.set_cache(True)
        self.operates(PlayerFollower, Transform, Hitbox)
    
    def process(self, player, chunks):
        for ent, chunk, (pf, tr, hitbox) in self.get_components(0, chunks=chunks):
            if pf.started_following:
                if ticks() - pf.last_followed >= pf.follow_delay:
                    if hitbox.centerx > player.rect.centerx and tr.vel[0] > 0:
                        tr.vel[0] *= -1
                    elif hitbox.centerx < player.rect.centerx and tr.vel[0] < 0:
                        tr.vel[0] *= -1
                    pf.started_following = False
            else:
                pf.last_followed = ticks()
                pf.started_following = True


@system(cache=True)
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


@system(cache=True)
class CollisionSystem:
    def __init__(self):
        self.set_cache(True)
        self.operates(CollisionFlag, Transform, Sprite)  # regular collisions and senders
        self.operates(CollisionFlag, Transform, Sprite, Health)  # collisions of receivers
        self.operates(Transform, Hitbox, Sprite, Headbutter)  # headbutting entities
    
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
                                chunk=None
                            )
                            # check if the receiver is dead, if so, kill it
                            if r_health.value <= 0:
                                self.delete(1, r_ent, r_chunk)
                            # make the bullet inactive
                            s_col_flag.set(CollisionFlags.INACTIVE)
        # check the headbutters
        for ent, chunk, (tr, hitbox, sprite, butt) in self.get_components(2, chunks=chunks):
            # check for collision with the player
            if player.rect.colliderect(hitbox):
                player.yvel = -10


@system(cache=True)
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


@system(cache=True)
class DropSystem:
    def __init__(self, display):
        self.display = display
        self.set_cache(True)
        self.operates(Drop, Hitbox)
    
    def process(self, player, scroll, chunks):
        for ent, chunk, arch, (drop, hitbox) in self.get_components(0, chunks=chunks, archetype=True):
            if hitbox.colliderect(player.rect):
                player.inventory.add(drop.block, 1)
                self.delete(arch, ent, chunk)


@system(cache=True)
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
