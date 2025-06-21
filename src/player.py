import pygame
import yaml
#
from pyengine.ecs import *
#
from .engine import *
from .entities import *
from .window import window
from .blocks import BF, inventory_img, bwand
from .midblit import MBT
from .tools import *



def cyclic(l):
    return {l[i]: l[(i + 1) % len(l)] for i in range(len(l))} 


class Direction(Enum):
    NONE = auto()
    LEFT = auto()
    RIGHT = auto()


class Action(Enum):
    NONE = auto()
    PLACE = auto()
    BREAK = auto()
    INTERACT = auto()


class MoveMode(Enum):
    NORMAL = auto()
    ROPE = auto()


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
        self.anim_skin = "samurai"
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
        self.move_mode = MoveMode.NORMAL
        # keyboard input
        self.jumps_left = 2
        self.pressing_jump = False
        # interaction with blocks
        self.action = Action.NONE
        self.inventory = Inventory()
        self.inventory.add("dynamite", 10)
        self.last_placed = []
    
    def update(self, display, dt):
        self.move(dt)
        self.edit(display)
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
        if not self.game.disable_input:
            if event.type == pygame.MOUSEBUTTONDOWN:
                # right mouse button
                if event.button == 3:
                    self.interact()

            elif event.type == pygame.MOUSEBUTTONUP:
                self.action = Action.NONE
                self.world.breaking.index = None
                self.world.breaking.pos = None
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.anim_skin = cyclic(["_default", "samurai", "nutcracker"])[self.anim_skin]
            
            elif event.key == pygame.K_f:
                # interact key
                self.f_interact()
    
    def f_interact(self):
        for rect, base in self.world.get_blocks_around(self.rect, range_x=(-3, 4), range_y=(-3, 4), return_name=True):
            if self.rect.colliderect(rect):
                # check which interaction to do
                if base == "rope":
                    if self.move_mode == MoveMode.NORMAL:
                        # attach to rope
                        self.move_mode = MoveMode.ROPE
                    else:
                        # detach from rope
                        self.move_mode = MoveMode.NORMAL
                    break
    
    def interact(self):
        if self.game.substate == Substates.PLAY:
            # get mouse data
            mouse = pygame.mouse.get_pos()
            mouses = pygame.mouse.get_pressed()
            chunk_index, block_pos = self.world.screen_pos_to_tile(mouse, self.game.scroll)
            base, mods = blocks.norm(self.world.data[chunk_index].get(block_pos, ""))

            if base == "dynamite":
                # make dynamite explode
                def detonate():
                    for xo, yo in self.world.get_radius_around(7):
                        new_chunk_index, new_block_pos = self.world.correct_tile(chunk_index, block_pos, xo, yo)
                        if self.world.exists(new_chunk_index, new_block_pos):
                            self.world.break_(new_chunk_index, new_block_pos)
                            time.sleep(10 ** -4)
                DThread(target=detonate).start()
            
            elif base == "workbench":
                self.game.midblit.set(MBT.WORKBENCH)

    def edit(self, display):
        if self.game.substate == Substates.PLAY:
            # get mouse data
            mouse = pygame.mouse.get_pos()
            mouses = pygame.mouse.get_pressed()
            
            # interact your mouse with the blocks
            if not self.game.disable_input:
                if mouses[0]:
                    # check where the mouse wants to place a block and whether it's prohibited
                    chunk_index, block_pos = self.world.screen_pos_to_tile(mouse, self.game.scroll)
                    base, mods = blocks.norm(self.world.data[chunk_index].get(block_pos, "air"))

                    # first decide what to do with the click depending on the block underneath
                    if self.action == Action.NONE:
                        # decide whether the first block you click on should be broken, edited, created on, etc.
                        if bwand(base, BF.EMPTY) or "b" in mods:
                            # the block should be placed
                            self.action = Action.PLACE
                        else:
                            # the block should be broken
                            self.action = Action.BREAK

                    # break the block
                    if self.action == Action.BREAK:
                        for xo, yo in product(range(0, 1), repeat=2):
                            new_chunk_index, new_block_pos = self.world.correct_tile(chunk_index, block_pos, xo, yo)
                            if new_block_pos in self.world.data[new_chunk_index]:
                                self.world.break_(new_chunk_index, new_block_pos)

                        if False and block_pos in self.world.data[chunk_index]:
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

                    # build a new block
                    elif self.action == Action.PLACE:
                        # check if block is not there or a background block
                        can_place = False
                        if bwand(self.world.data[chunk_index].get(block_pos, "air"), BF.EMPTY):
                            can_place = True
                        else:
                            base, mods = blocks.norm(self.world.data[chunk_index][block_pos])
                            if "b" in mods:
                                can_place = True
                        if can_place:
                            placed_name = "dynamite"
                            self.world.set(chunk_index, block_pos, placed_name)
                            self.process_placed_block(chunk_index, block_pos, placed_name)
                        
                    # edit the block
                    elif self.action == Action.INTERACT:
                        print("ASD")
    
    def process_placed_block(self, chunk_index, block_pos, block):
        if block == "karabiner":
            if self.last_placed:
                # there is already a karabiner placed down so connect
                k1_chunk_index, k1_block_pos, _ = self.last_placed
                d_block_pos = (block_pos[0] - self.last_placed[1][0], block_pos[1] - self.last_placed[1][1])
                # check whether the two karabiners are horizontally or vertically aligned
                if any(d_block_pos) and not all(d_block_pos):
                    # connect the karabiners with rope
                    if d_block_pos[0] > 0:
                        # connect horizontally
                        for xo in range(1, d_block_pos[0]):
                            new_chunk_index, new_block_pos = self.world.correct_tile(k1_chunk_index, k1_block_pos, xo, 0)
                            self.world.set(chunk_index, block_pos, "rope")
            self.last_placed = [chunk_index, block_pos, block]


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
        for rect in self.world.get_blocks_around(self.rect, range_x=(-3, 4), range_y=(-3, 4)):
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

        if self.move_mode == MoveMode.NORMAL:
            self.yvel += self.gravity
            self.rect.y += self.yvel

        # collision Y
        # TODO: the range of the collision in the y-direction to account for movement
        for rect in self.world.get_blocks_around(self.rect, range_x=(-3, 4), range_y=(-3, 4)):
            if self.rect.colliderect(rect):
                if self.yvel > 0:
                    self.rect.bottom = rect.top
                    self.jumps_left = 1
                    self.in_air = False
                else:
                    self.rect.top = rect.bottom
                self.yvel = 0
    
    def jump(self):
        self.yvel = -6
        self.jumps_left -= 1
        self.pressing_jump = True
