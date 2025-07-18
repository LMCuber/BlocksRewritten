from pygame._sdl2.video import Window, Renderer, Texture
import pygame


pygame.init()

win = Window(size=(800, 600))
ren = Renderer(win)
font = pygame.font.SysFont("Courier New", 20)
clock = pygame.time.Clock()

while True:
    clock.tick()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit()
    
    ren.draw_color = (120, 120, 120)

    ren.clear()

    surf = font.render(str(int(clock.get_fps())), True, (0, 0, 0))
    tex = Texture.from_surface(ren, surf)
    ren.blit(tex, pygame.Rect(0, 0, 50, 50))

    ren.present()
