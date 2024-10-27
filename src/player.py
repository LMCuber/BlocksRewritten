import pygame


class Player:
    def __init__(self, world):
        self.world = world
        self.image = pygame.Surface((30, 30))
        self.image.fill((19, 179, 172))
        self.rect = self.image.get_frect()
    
    def draw(self, display):
        display.blit(self.image, self.world.get_scroll(self.rect))
    
    def update(self, display):
        m = 2.5
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.rect.x -= m
        if keys[pygame.K_d]:
            self.rect.x += m
        if keys[pygame.K_w]:
            self.rect.y -= m
        if keys[pygame.K_s]:
            self.rect.y += m
        self.draw(display)
        