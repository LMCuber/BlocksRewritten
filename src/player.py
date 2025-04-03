import pygame
import yaml
#
from pyengine.ecs import *
#
from .engine import *
from .entities import *
from .window import window
from .blocks import BlockFlags, inventory_img



def cyclic(l):
    return {l[i]: l[(i + 1) % len(l)] for i in range(len(l))} 


class Direction(Enum):
    NONE = auto()
    LEFT = auto()
    RIGHT = auto()


class Action(Enum):
    PLACE = auto()
    BREAK = auto()
    NONE = auto()


class Inventory:
    def __init__(self):
        self.keys: list[str] = []
        self.values: list[int] = []
    
    def add(self, item, amount=1):
        if item in self.keys:
            # already in inventory
            self.values[self.keys.index(item)] += 1
        else:
            # doesnt exist, so add new
            self.keys.append(item)
            self.values.append(amount)
    
    def update(self, display):
        # inventory image
        mouse = pygame.mouse.get_pos()
        topleft = (300, 10)
        display.blit(inventory_img, topleft)
        x, y = topleft[0] + S * 2, topleft[1] + S * 2
        rects = []
        # blocks in the inventory
        for i, (block, amount) in enumerate(zip(self.keys, self.values)):
            # render the block
            blit_pos = (x + i * (BS + S * 4), y)
            display.blit(blocks.images[block], blit_pos)
            rects.append(pygame.Rect(*blit_pos, BS + S * 2, BS + S * 2))
            # write the block amount
            write(display, "center", amount, fonts.orbitron[13], WHITE, blit_pos[0] + BS / 2, blit_pos[1] + BS / 2)
            # write the tooltip
            if rects[-1].collidepoint(mouse):
                write(display, "topleft", block, fonts.orbitron[15], WHITE, mouse[0] + 20, mouse[1] + 20)


class Player:
    def __init__(self, game, world, menu):
        # pointers to lobal game objects
        self.game = game
        self.world = world
        self.menu = menu
        # animation parameters
        self.anim_index = 0  # index of spritesheet
        self.anim_skin = "nutcracker"
        self.anim_mode = "idle"  # e.g. walk, run, attack 1, etc.
        # image, rectangle, hitbox, whatever
        self.images = AnimData.get(self.anim_skin, self.anim_mode)
        self.rect = pygame.FRect((0, -100, 52, 70))
        # ECS?!
        # self.sprite = Sprite.from_path(Path("res", "images", "player_animations", self.anim_skin, f"{self.anim_mode}.png")),
        # physics
        self.yvel = 0
        self.xvel = 0
        self.gravity = glob.gravity
        # keyboard input
        self.jumps_left = 2
        self.pressing_jump = False
        # actions with blocks
        self.action = Action.NONE
        self.inventory = Inventory()
    
    def update(self, display, block_rects, dt):
        self.move(dt)
        self.interact(display, block_rects)
        self.draw(display)
        self.inventory.update(display)

    def draw(self, display):
        # get the current animation image
        self.images, offset, anim_vel, _ = AnimData.get(self.anim_skin, self.anim_mode)
        self.anim_index += anim_vel
        try:
            image = self.images[int(self.anim_index)]
        except IndexError:
            self.anim_index = 0
        finally:
            image = self.images[int(self.anim_index)]
        # flip the image if player is moving to the left instead of to the right
        if self.xvel < 0:
            image = pygame.transform.flip(image, True, False)
        # render the player
        self.scrolled_rect = self.rect.move(-self.game.scroll[0], -self.game.scroll[1])
        image_rect = image.get_rect(center=self.scrolled_rect.center).move(0, offset)
        display.blit(image, image_rect)
        
        # show the hitboxes
        if self.menu.hitboxes.checked:
            # scrolled_rect = hitbox (ORANGE), image_rect = actual blit position (LIGHT_GREEN)
            pygame.draw.rect(window.display, ORANGE, self.scrolled_rect, 1)
            pygame.draw.rect(window.display, LIGHT_GREEN, image_rect, 1)
    
    def process_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.action == Action.NONE:
                    self.action = Action.BREAK

                return
                # shoow a bullet entity
                m = pygame.mouse.get_pos()
                dy = m[1] - window.height / 2
                dx = m[0] - window.width / 2
                m = 10
                for ao in range(1):
                    angle = atan2(dy, dx)
                    xvel = cos(angle + ao * 0.1) * m
                    yvel = sin(angle + ao * 0.1) * m
                    create_entity(
                        CollisionFlag(CollisionFlags.SEND),
                        Transform([self.rect.centerx, self.rect.centery], [xvel, yvel], TransformFlag(TransformFlags.PROJECTILE), 0.03),
                        Sprite.from_path(Path("res", "images", "bullet.png"), 1, 0.1),
                        chunk=0
                    )

            elif event.button == 3:
                if self.action == Action.NONE:
                    self.action = Action.PLACE

        elif event.type == pygame.MOUSEBUTTONUP:
            self.action = Action.NONE
            self.world.breaking.index = None
            self.world.breaking.pos = None
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.anim_skin = cyclic(["_default", "samurai", "nutcracker"])[self.anim_skin]
    
    def interact(self, display, block_rects):
        if self.game.substate == Substates.PLAY:
            # get mouse data
            mouse = pygame.mouse.get_pos()
            mouses = pygame.mouse.get_pressed()
            if mouses[0] or mouses[2]:
                # check where the mouse wants to place a block and whether it's prohibited
                chunk_index, block_pos = self.world.screen_pos_to_tile(mouse, self.game.scroll)
                # place or break block
                if mouses[0]:
                    if self.action == Action.BREAK:
                        # for xo, yo in product(range(-1, 2), repeat=2):
                        #     new_chunk_index, new_block_pos = self.world.correct_tile(chunk_index, block_pos, xo, yo)
                        #     if new_block_pos in self.world.data[new_chunk_index]:
                        #         del self.world.data[new_chunk_index][new_block_pos]
                        if block_pos in self.world.data[chunk_index]:
                            # del self.world.data[chunk_index][block_pos]
                            # increase the world breaking
                            if (chunk_index, block_pos) == (self.world.breaking.index, self.world.breaking.pos):
                                # break block since it already began breaking
                                self.world.breaking.anim += 0.07
                            else:
                                # switch to new block
                                self.world.breaking.index = chunk_index
                                self.world.breaking.pos = block_pos
                                self.world.breaking.anim = 0
                elif mouses[2]:
                    if self.action == Action.PLACE:
                        self.world.data[chunk_index][block_pos] = "dynamite"

    def move(self, dt):
        # init
        keys = pygame.key.get_pressed()
        
        # movement X
        self.max_xvel = 2.1
        self.direc = Direction.NONE
        if keys[pygame.K_a]:
            self.xvel = -self.max_xvel
            self.rect.x += self.xvel
            self.direc = Direction.LEFT
        if keys[pygame.K_d]:
            self.xvel = self.max_xvel
            self.rect.x += self.xvel
            self.direc = Direction.RIGHT
        if not (keys[pygame.K_a] or keys[pygame.K_d]):
            self.anim_mode = "idle"
            self.anim_index = 0
        else:
            self.anim_mode = "run"
        
        # collision X
        for rect in self.world.get_blocks_around(self.rect, range_x=(-3, 3), range_y=(-3, 3)):
            if self.rect.colliderect(rect):
                if self.direc == Direction.RIGHT:
                    self.rect.right = rect.left
                else:
                    self.rect.left = rect.right

        # movement X
        if keys[pygame.K_w]:
            if self.jumps_left > 0 and not self.pressing_jump:
                self.jump()
        else:
            self.pressing_jump = False

        self.yvel += self.gravity
        self.rect.y += self.yvel

        # collision Y
        # TODO: the range of the collision in the y-direction to account for movement
        for rect in self.world.get_blocks_around(self.rect, range_x=(-3, 3), range_y=(-3, 3)):
            if self.rect.colliderect(rect):
                if self.yvel > 0:
                    self.rect.bottom = rect.top
                    self.jumps_left = 2
                    self.in_air = False
                else:
                    self.rect.top = rect.bottom
                self.yvel = 0
    
    def jump(self):
        self.yvel = -6
        self.jumps_left -= 1
        self.pressing_jump = True
