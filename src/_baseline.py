# Example file showing a basic pygame "game loop"
import pygame

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1280, 720), pygame.FULLSCREEN)
clock = pygame.time.Clock()
running = True
font = pygame.font.SysFont("Courier New", 40)

while running:
    clock.tick() # limits FPS to 60

    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("purple")
    screen.blit(font.render(str(int(clock.get_fps())), True, (0, 0, 0)), (40, 40))

    # RENDER YOUR GAME HERE

    # flip() the display to put your work on screen
    pygame.display.update()


pygame.quit()