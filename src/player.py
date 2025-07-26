import pygame
import yaml
#
from pyengine.ecs import *
#
from .engine import *
from .entities import *
from .window import window
from .blocks import BF, inventory_img, bwand, nbwand, X
from .midblit import MBT
from .tools import *


class Direction(Enum):
    NONE = auto()
    LEFT = auto()
    RIGHT = auto()


class BlockAction(Enum):
    NONE = auto()
    PLACE = auto()
    BREAK = auto()
    INTERACT = auto()


class Action(Enum):
    TERRAIN = auto()
    ATTACK = auto()


class MoveMode(Enum):
    NORMAL = auto()
    ROPE = auto()


class Inventory:
    def __init__(self, player):
        self.player = player
        self.game = self.player.game

        self.max_items = 11
        self.keys: list[str] = []
        self.values: list[int] = []
        self.index: int = 0
    
    def __getitem__(self, key):
        return self.keys[key]

    @property
    def current(self):
        return self[self.index]

    @property
    def current_amount(self):
        return self.values[self.index]

    @property
    def num_items(self):
        return len(list(filter(None, self.values)))  # gets all truthy elements from self.values and returns its length
    
    @property
    def can_add(self):
        return self.num_items < self.max_items
    
    def use(self):
        self.values[self.index] -= 1
    
    def add(self, item, amount=1):
        if not self.can_add:
            return
        if item in self.keys:
            # already in inventory
            self.values[self.keys.index(item)] += 1
        else:
            # doesnt exist, so add new
            self.keys.append(item)
            self.values.append(amount)
    
    def slide(self, amount):
        self.index += amount
        if amount > 0:
            self.index = min(self.index, self.num_items - 1)
        else:
            self.index = max(self.index, 0)
    
    def update(self, display):
        # inventory image
        mouse = pygame.mouse.get_pos()
        inv_rect = inventory_img.get_rect(midtop=(window.width / 2, 20))
        display.blit(inventory_img, inv_rect)
        x, y = inv_rect.x + S * 2, inv_rect.y + S * 2
        rects = []

        # blocks in the inventory
        for i, (name, amount) in enumerate(zip(self.keys, self.values)):
            # render the block
            blit_pos = (x + i * (BS + S * 4), y)
            rects.append(blocks.images[name].get_rect(topleft=blit_pos))
            display.blit(blocks.images[name], rects[-1])

            # write the block amount
            pgb.write(display, "center", amount, fonts.orbitron[13], WHITE, blit_pos[0] + BS / 2, blit_pos[1] + BS / 2)

            # only applicable to selected block
            if i == self.index:
                if self.player.action == Action.TERRAIN:
                    # selected rectangle
                    pgb.draw_rect(display, WHITE, (blit_pos[0] - S, blit_pos[1] - S, BS + S * 2, BS + S * 2), S)

                # display the name with text
                pgb.write(display, "midtop", blocks.repr(name), fonts.orbitron[16], self.game.stat_color, window.width / 2, 70)


class Player:
    def __init__(self, game, world, menu):
        # dependency injection
        self.game = game
        self.world = world
        self.menu = menu
        # animation parameters
        self.anim_index = 0  # index of spritesheet
        self.anim_skin = "_default"
        self.anim_mode = "idle"  # e.g. walk, run, attack 1, etc.
        # image, rectangle, hitbox, whatever
        self.images = AnimData.get(self.anim_skin, self.anim_mode)
        self.rect = pygame.FRect((0, -100, 52, 70))
        self.blit_rect = pygame.Rect(0, 0, 0, 0)
        # physics
        self.yvel = 0
        self.xvel = 0
        self.gravity = glob.gravity
        self.move_mode = MoveMode.NORMAL
        # keyboard input
        self.jumps_left = 2
        self.pressing_jump = False
        # interaction with blocks
        self.block_action = BlockAction.NONE
        self.action = Action.TERRAIN
        self.action_when_clicked = None
        self.inventory = Inventory(self)
        self.inventory.add("torch", 99)
        self.last_placed = []
    
    def update(self, display, dt):
        self.move(dt)
        self.edit(display)
        self.draw(display, dt)

    def draw(self, display, dt):
        # get the current animation image
        self.images, self.fimages, offset, anim_vel, hitboxes = AnimData.get(self.anim_skin, self.anim_mode)
        self.anim_index += anim_vel * dt
        try:
            self.images[int(self.anim_index)]
        except IndexError:
            self.anim_index = 0
        if self.xvel > 0:
            image = self.images[int(self.anim_index)]
        else:
            image = self.fimages[int(self.anim_index)]
        
        # render the player
        self.scrolled_rect = self.rect.move(-self.game.scroll[0], -self.game.scroll[1])
        self.blit_rect = self.images[int(self.anim_index)].get_rect(center=self.scrolled_rect.center).move(0, offset)
        display.blit(image, self.blit_rect)
        
        # show the hitboxes
        if self.menu.hitboxes.checked:
            # scrolled_rect = hitbox and movement (ORANGE), image_rect = blit position (LIGHT_GREEN)
            pgb.draw_rect(window.display, ORANGE, self.scrolled_rect, 1)
            pgb.draw_rect(window.display, LIGHT_GREEN, self.blit_rect, 1)
    
    def attack(self, event):
        if event.button == 1:
            dy = pygame.mouse.get_pos()[1] - self.blit_rect.centery
            dx = pygame.mouse.get_pos()[0] - self.blit_rect.centerx
            angle = atan2(dy, dx)
            m = 10
            create_entity(
                Transform([0, 0], [m * cos(angle), m * sin(angle)], gravity=glob.gravity * 0.1),
                Hitbox(self.rect.center, (0, 0)),
                Sprite.from_img(pgb.scale_by(imgload("res", "images", "bullet.png"), 3)),
                Projectile(37),
                Disappear.default(),
                chunk=self.world.pos_to_tile(self.rect.center)[0]
            )
            
    def process_event(self, event):
        if not self.game.disable_input:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.action_when_clicked = self.action
                # right mouse button
                if event.button == 3:
                    self.interact()

                # attack
                if self.action == Action.ATTACK:
                    self.attack(event)
                
            elif event.type == pygame.MOUSEBUTTONUP:
                self.block_action = BlockAction.NONE
                self.world.breaking.index = None
                self.world.breaking.pos = None
                self.action_when_clicked = None
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # self.anim_skin = cyclic(["_default", "samurai", "nutcracker", "ra"])[self.anim_skin]
                # drop_img = pygame.transform.scale_by(blocks.images["soil_f"], 0.5)
                # for _ in range(1000):
                #     create_entity(
                #         Transform([300, 300], [0, 0], gravity=0.03, sine=(0.35, 4)),
                #         Hitbox((-rand(-50, 50), 0), (0, 0), anchor="midbottom"),
                #         Sprite.from_img(drop_img),
                #         # Drop("soil_f"),
                #         chunk=None
                #     )
                self.action = cyclic((Action.TERRAIN, Action.ATTACK))[self.action]
                if self.action == Action.TERRAIN:
                    pygame.mouse.set_cursor(pygame.cursors.tri_left)
                elif self.action == Action.ATTACK:
                    pygame.mouse.set_cursor(pygame.cursors.broken_x)
            
            elif event.key == pygame.K_f:
                # interact key
                self.f_interact()
            
            elif event.key in [getattr(pygame, f"K_{n}") for n in range(1, 10)]:
                index = event.key - 49
                if index < self.inventory.num_items:
                    self.inventory.index = index
        
        elif event.type == pygame.MOUSEWHEEL:
            self.inventory.slide(-event.y)
            
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
                    if self.action == Action.TERRAIN and self.action_when_clicked == Action.TERRAIN:
                        # check where the mouse wants to place a block and whether it's prohibited
                        chunk_index, block_pos = self.world.screen_pos_to_tile(mouse, self.game.scroll)
                        base, mods = blocks.norm(self.world.data[chunk_index].get(block_pos, "air"))

                        # first decide what to do with the click depending on the block underneath
                        if self.block_action == BlockAction.NONE:
                            # decide whether the first block you click on should be broken, edited, created on, etc.
                            if bwand(base, BF.EMPTY) or "b" in mods:
                                if nbwand(base, BF.UNPLACABLE):
                                    # the block should be placed
                                    self.block_action = BlockAction.PLACE
                            else:
                                # the block should be broken
                                self.block_action = BlockAction.BREAK

                        # break the block
                        if self.block_action == BlockAction.BREAK:
                            for xo, yo in product(range(-1, 2), repeat=2):
                                new_chunk_index, new_block_pos = self.world.correct_tile(chunk_index, block_pos, xo, yo)
                                if new_block_pos in self.world.data[new_chunk_index]:
                                    self.world.break_(new_chunk_index, new_block_pos)
                            if not (bwand(base, BF.EMPTY) or "b" in mods) and False:
                                if block_pos in self.world.data[chunk_index]:
                                    # increase the world breaking
                                    if (chunk_index, block_pos) == (self.world.breaking.index, self.world.breaking.pos):
                                        # break block since it already began breaking
                                        self.world.breaking.anim += 10
                                    else:
                                        # switch to new block
                                        self.world.breaking.index = chunk_index
                                        self.world.breaking.pos = block_pos
                                        self.world.breaking.anim = 0

                        # build a new block
                        elif self.block_action == BlockAction.PLACE:
                            # check if block is not there or a background block
                            can_place = False
                            if bwand(self.world.data[chunk_index].get(block_pos, "air"), BF.EMPTY):
                                can_place = True
                            else:
                                base, mods = blocks.norm(self.world.data[chunk_index][block_pos])
                                if "b" in mods:
                                    can_place = True
                                    
                            if self.inventory.current_amount > 0:
                                if can_place:
                                    placed_name = self.inventory.current
                                    self.world.set(chunk_index, block_pos, placed_name)
                                    self.process_placed_block(chunk_index, block_pos, placed_name)
                                    self.inventory.use()
                            
                        # edit the block
                        elif self.block_action == BlockAction.INTERACT:
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
            self.rect.x += self.xvel * dt
            self.direc = Direction.LEFT
        if keys[pygame.K_d]:
            self.xvel = self.max_xvel
            self.rect.x += self.xvel * dt
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
            # accounting for the dt curve
            self.yvel += self.gravity * dt * 0.5
            self.rect.y += self.yvel * dt
            self.yvel += self.gravity * dt * 0.5
            ...

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
