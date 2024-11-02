import pygame
from .engine import *


class Player:
    def __init__(self, world):
        # formalities
        self.world = world
        # image, rectangle, hitbox, whatever
        self.image = pygame.Surface((30, 30))
        self.image.fill((19, 179, 172))
        self.rect = self.image.get_frect(topleft=(0, -100))
        # physics
        self.yvel = 0
        self.xvel = 0
        self.gravity = glob.gravity
        # keyboard input
        self.jumps_left = 2
        self.pressing_jump = False
    
    def draw(self, display, scroll):
        display.blit(self.image, (self.rect.x - scroll[0], self.rect.y - scroll[1]))
    
    def move(self, scroll, dt):
        # init
        keys = pygame.key.get_pressed()
        
        # movement X
        self.max_xvel = 2.4
        self.xacc = 0.2
        if keys[pygame.K_a]:
            self.xvel += (-self.max_xvel - self.xvel) * self.xacc
        if keys[pygame.K_d]:
            self.xvel += (self.max_xvel - self.xvel) * self.xacc
        if not (keys[pygame.K_a] or keys[pygame.K_d]):
            self.xvel += -self.xvel * self.xacc
        self.rect.x += self.xvel
        
        # collision X
        for rect in get_blocks_around(self.rect, self.world):
            if self.rect.colliderect(rect):
                if self.xvel > 0:
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
        for rect in get_blocks_around(self.rect, self.world):
            if self.rect.colliderect(rect):
                if self.yvel > 0:
                    self.rect.bottom = rect.top
                    self.jumps_left = 2
                    self.in_air = False
                else:
                    self.rect.top = rect.bottom
                self.yvel = 0
    
    def jump(self):
        self.yvel = -5
        self.jumps_left -= 1
        self.pressing_jump = True
    
    def update(self, display, scroll, dt):
        self.move(scroll, dt)
        self.draw(display, scroll)
        