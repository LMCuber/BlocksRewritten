class Player:
    def __init__(self):
        self.image = pygame.Surface((30, 30))
        self.image.fill((19, 179, 172))
    
    def draw(self, display):
        display.blit(self.image, self.rect)
    
    def update(self, display):
        self.draw(display)