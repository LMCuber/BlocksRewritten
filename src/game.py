import pygame
import tomllib as toml
from pathlib import Path
import sys
#
from pyengine.pgshaders import *
from pyengine.pgbasics import *
import pyengine.pgwidgets as pgw
#
from src.entities import *
from src.window import *
from src.shock import *
from src import world
from src import player
from src import fonts
from src import joystick



class Game:
    def __init__(self):
        self.widget_kwargs = {"font": fonts.orbitron[20], "anchor": "topleft"}
        self.clock = pygame.time.Clock()
        self.init_systems()
        self.shader = ModernglShader(Path("src", "shaders", "vertex.glsl"), Path("src", "shaders", "fragment.glsl"))
        self.shock_gradient = imgload("res", "images", "visuals", "shock_gradient.jpg")
        # runtime objects
        self.world = world.World()
        self.player = player.Player(self.world)
        self.scroll = [0, 0]
        self.shock = Shock(0, 0, 0, [0, 0])
        self.last_start = ticks()
        # joystick
        self.joystick = joystick.JoystickManager()
    
    def init_systems(self):
        self.render_system = RenderSystem(window.display)
        self.player_follower_system = PlayerFollowerSystem(window.display)
    
    def send_data_to_shader(self):
        # send textures to the shader
        self.shader.send_surf(0, "tex", window.display)
        self.shader.send_surf(1, "paletteTex", blocks.palette_img)

        # send uniform data to the shader
        self.shader.send("time", ticks())
        # self.shader.send("centerWin", window.center)
        self.shader.send("res", (window.width, window.height))

        w = 120
        self.shader.send("deadZone", (pygame.mouse.get_pos()[0] - w, pygame.mouse.get_pos()[1] - w, w * 2, w * 2))
        o = 0
        self.shader.send("rOffset", (-o, 0))
        self.shader.send("gOffset", (0, 0))
        self.shader.send("bOffset", (o, 0))
        # self.shader.send("lightPosWin", self.player.rect.move(-self.scroll[0], -self.scroll[1]).center)
        # self.shader.send("lightPowerWin", 0)

    def apply_scroll(self, m):
        self.scroll[0] += (self.player.rect.x - self.scroll[0] - window.width / 2 + self.player.rect.width / 2) * m
        self.scroll[1] += (self.player.rect.y - self.scroll[1] - window.height / 2 + self.player.rect.height / 2) * m
    
    def quit(self):
        pygame.quit()
        sys.exit()
            
    def mainloop(self):
        self.running = True
        while self.running:
            dt = self.clock.tick() / (1 / 144 * 1000)

            for event in pygame.event.get():
                pgw.process_widget_events(event)
                self.player.process_event(event)

                if event.type == pygame.QUIT:
                    self.running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                
                elif event.type == pygame.VIDEORESIZE:
                    print(event.size)
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # shock_pos = [event.pos[0] / window.width, event.pos[1] / window.height]
                    # self.shock = Shock(0, 0, 0, shock_pos, active=True)
                    pass

            window.display.fill(SKY_BLUE)

            # scroll the display
            self.apply_scroll(0.1)

            # draw and update the terrain
            num_blocks, processed_chunks = self.world.update(window.display, self.scroll)
            processed_chunks.append(0)

            # update the player
            self.player.update(window.display, self.scroll, dt)

            # process the ECS systems
            self.render_system.process(self.scroll, self.world, chunks=processed_chunks)
            self.player_follower_system.process(self.player, chunks=processed_chunks)

            # update the pyengine.pgwidgets
            pgw.draw_and_update_widgets()

            # display the fps
            write(window.display, "topleft", int(self.clock.get_fps()), fonts.orbitron[20], BLACK, 5, 5)
            if window.vsync:
                write(window.display, "topleft", "vsync", fonts.orbitron[10], BLACK, 5, 24)
            write(window.display, "topleft", f"{num_blocks} blocks", fonts.orbitron[15], BLACK, 5, 40)

            # --- DO RENDERING BEFORE THIS BLOCK ---
            self.send_data_to_shader()

            # render the shader
            self.shader.render()

            # window.window.flip()
            pygame.display.flip()

            self.shader.release_all_textures()
        
        self.quit()
