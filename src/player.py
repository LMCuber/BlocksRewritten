import pygame
#
from pyengine.ecs import *
#
from .engine import *
from .entities import *
from .window import window


class Direction(Enum):
    NONE = auto()
    LEFT = auto()
    RIGHT = auto()


class AnimMode(Enum):
    RUN = auto()
    IDLE = auto()


class AnimData:
    RUN = imgload("res", "images", "player_animations", "samurai", "run.png", scale=S, frames=8)
    IDLE = imgload("res", "images", "player_animations", "samurai", "idle.png", scale=S, frames=1)

    @classmethod
    def get(cls, attr: AnimMode):
        return getattr(cls, attr.name)


class Action(Enum):
    PLACE = auto()
    BREAK = auto()
    NONE = auto()


class Player:
    def __init__(self, game, world, menu):
        # pointers to lobal game objects
        self.game = game
        self.world = world
        self.menu = menu
        # animation parameters
        self.anim_index = 0  # index of spritesheet
        self.anim_vel = 0.08  # animation speed
        self.anim_mode = AnimMode.IDLE  # e.g. walk, run, attack 1, etc.
        # image, rectangle, hitbox, whatever
        self.images = AnimData.get(self.anim_mode)
        # self.rect = self.images[0].get_frect(topleft=(0, -100))
        self.rect = pygame.FRect((0, -100, 80, 80))
        # physics
        self.yvel = 0
        self.xvel = 0
        self.gravity = glob.gravity
        # keyboard input
        self.jumps_left = 2
        self.pressing_jump = False
        # actions with blocks
        self.action = Action.NONE
    
    def draw(self, display):
        # get the current animation image
        self.images = AnimData.get(self.anim_mode)
        self.anim_index += self.anim_vel
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
        self.game.scrolled_rect = self.rect.move(-self.game.scroll[0], -self.game.scroll[1])
        image_rect = image.get_rect(center=self.game.scrolled_rect.center)
        display.blit(image, image_rect)
        
        # show the hitboxes
        if self.menu.hitboxes.checked:
            pygame.draw.rect(window.display, LIGHT_GREEN, self.game.scrolled_rect, 1)
            # pygame.draw.rect(window.display, ORANGE, image_rect, 1)
    
    def process_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.action == Action.NONE:
                    self.action = Action.BREAK

                """
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
                        Sprite(Path("res", "images", "bullet.png"), 1, 0.1),
                        chunk=0
                    )
                """
            elif event.button == 3:
                if self.action == Action.NONE:
                    self.action = Action.PLACE

        elif event.type == pygame.MOUSEBUTTONUP:
            self.action = Action.NONE
    
    def interact(self, block_rects):
        if self.game.substate == Substates.PLAY:
            # get mouse data
            mouse = pygame.mouse.get_pos()
            mouses = pygame.mouse.get_pressed()
            if mouses[0] or mouses[2]:
                chunk_index, block_pos = self.world.screen_pos_to_tile(mouse, self.game.scroll)
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
            self.anim_mode = AnimMode.IDLE
        else:
            self.anim_mode = AnimMode.RUN
        
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

        self.yvel += self.gravity
        self.rect.y += self.yvel

        # collision Y
        # TODO: the range of the collision in the y-direction to account for movement
        for rect in self.world.get_blocks_around(self.rect, range_x=(-3, 4), range_y=(-3, 4)):
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
    
    def update(self, display, block_rects, dt):
        self.move(dt)
        self.interact(block_rects)
        self.draw(display)
        