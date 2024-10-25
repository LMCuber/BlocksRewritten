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



class Game:
    def __init__(self):
        self.widget_kwargs = {"font": fonts.orbitron[20], "anchor": "topleft"}

        with open(Path("src", "settings.toml"), "rb") as f:
            toml_data = toml.load(f)
            for attr, value in toml_data["game"].items():
                setattr(self, attr, value)
        
        pygame.init()
        self.clock = pygame.time.Clock()
        self.create_window()
        self.init_systems()
        self.shader = ModernglShader(Path("src", "shaders", "vertex.glsl"), Path("src", "shaders", "fragment.glsl"))
        self.slider = pgw.Slider(self.display, "Slide me!", range(0, 21), 0, pos=(560, 20), width=250, height=80, **self.widget_kwargs)
        self.world = world.World()
    
    def init_systems(self):
        self.render_system = RenderSystem(self.display)
    
    def create_window(self):
        pygame.display.set_caption("Blockingdom")
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 0)
        self.window = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.WINDOW_CENTER = (self.WINDOW_WIDTH / 2, self.WINDOW_HEIGHT / 2)
        self.display = pygame.display.get_surface()
        self.display.fill((40, 40, 40))
    
    def send_data_to_shader(self):
        # send textures to the shader
        self.shader.send_surf(0, "tex", self.display)
        self.shader.send_surf(1, "paletteTex", blocks.palette_img)

        # send uniform data to the shader
        self.shader.send("time", ticks())
        self.shader.send("center", self.WINDOW_CENTER)
        self.shader.send("res", (self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        w = 120
        self.shader.send("deadZone", (pygame.mouse.get_pos()[0] - w, pygame.mouse.get_pos()[1] - w, w * 2, w * 2))
        # o = sin(ticks() * 0.001) * -self.slider.value
        # self.shader.send("rOffset", (-o, 0))
        # self.shader.send("gOffset", (0, 0))
        # self.shader.send("bOffset", (o, 0))
    
    def quit(self):
        pygame.quit()
        sys.exit()
            
    def mainloop(self):
        self.running = True
        while self.running:
            self.clock.tick()

            for event in pygame.event.get():
                pgw.process_widget_events(event)

                if event.type == pygame.QUIT:
                    self.running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                
                elif event.type == pygame.VIDEORESIZE:
                    print(event.size)

            self.display.fill((60, 120, 50))

            self.render_system.process()

            # display the fps
            write(self.display, "topleft", int(self.clock.get_fps()), fonts.orbitron[20], BLACK, 5, 5)

            # draw and update the terrain
            self.world.update(self.display)

            # update the pyengine widgets
            pgw.draw_and_update_widgets()

            # guess
            self.send_data_to_shader()

            # render the shader
            self.shader.render()

            pygame.display.flip()

            self.shader.release_all_textures()