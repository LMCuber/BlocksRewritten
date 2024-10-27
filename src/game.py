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
from src import world
from src import fonts
from src.player import *
from src.window import *



class Game:
    def __init__(self, vsync=False):
        self.widget_kwargs = {"font": fonts.orbitron[20], "anchor": "topleft"}

        with open(Path("src", "settings.toml"), "rb") as f:
            toml_data = toml.load(f)
            window.create_window(**toml_data["window"])
        
        pygame.init()
        self.clock = pygame.time.Clock()
        self.vsync = vsync
        self.init_systems()
        self.shader = ModernglShader(Path("src", "shaders", "vertex.glsl"), Path("src", "shaders", "fragment.glsl"))
        self.slider = pgw.Slider(window.display, "Slide me!", range(0, 21), 0, pos=(560, 20), width=250, height=80, **self.widget_kwargs)
        self.world = world.World()
        self.player = Player(self.world)
    
    def init_systems(self):
        self.render_system = RenderSystem(window.display)
    
    def send_data_to_shader(self):
        # send textures to the shader
        self.shader.send_surf(0, "tex", window.display)
        self.shader.send_surf(1, "paletteTex", blocks.palette_img)

        # send uniform data to the shader
        self.shader.send("time", ticks())
        self.shader.send("center", window.center)
        self.shader.send("res", (window.width, window.height))
        w = 120
        self.shader.send("deadZone", (pygame.mouse.get_pos()[0] - w, pygame.mouse.get_pos()[1] - w, w * 2, w * 2))
        o = sin(ticks() * 0.001) * -self.slider.value
        o = self.slider.value
        self.shader.send("rOffset", (-o, 0))
        self.shader.send("gOffset", (0, 0))
        self.shader.send("bOffset", (o, 0))
    
    def quit(self):
        pygame.quit()
        sys.exit()
            
    def mainloop(self):
        self.running = True
        while self.running:
            self.clock.tick(window.target_fps)

            for event in pygame.event.get():
                pgw.process_widget_events(event)

                if event.type == pygame.QUIT:
                    self.running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                
                elif event.type == pygame.VIDEORESIZE:
                    print(event.size)

            window.display.fill((60, 120, 50))

            self.render_system.process()

            # draw and update the terrain
            self.world.update(window.display)

            # update the player
            self.player.update(window.display)

            # update the pyengine widgets
            pgw.draw_and_update_widgets()

            # display the fps
            write(window.display, "topleft", int(self.clock.get_fps()), fonts.orbitron[20], BLACK, 5, 5)
            if self.vsync:
                write(window.display, "topleft", "vsync", fonts.orbitron[10], BLACK, 5, 24)

            # DO RENDERING BEFORE THIS BLOCK
            self.send_data_to_shader()

            # render the shader
            self.shader.render()

            pygame.display.flip()

            self.shader.release_all_textures()
