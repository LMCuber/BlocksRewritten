import pygame
from pathlib import Path
import tomllib as toml
from random import uniform as randf
from math import sin, pi
from pyengine.pgbasics import set_pyengine_hwaccel
import ctypes
import platform


pygame.init()


class Window:
    def create_window(self, width, height, fullscreen, vsync, fps_cap):
        # windows
        # ctypes.windll.user32.SetProcessDPIAware()
        # set PyEngine hwaccel flag
        set_pyengine_hwaccel(False)
        # pygame window and OpenGL flags
        pygame.display.set_caption("Blockingdom")
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, vsync)
        # window parameters
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        if self.fullscreen:
            self.width = pygame.display.Info().current_w
            self.height = pygame.display.Info().current_h
        self.size = (self.width, self.height)
        self.vsync = vsync
        self.fps_cap = fps_cap
        self.center = (self.width / 2, self.height / 2)
        self.window = pygame.display.set_mode((self.width, self.height), 
            pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE,
            vsync=self.vsync
        )
        self.display = pygame.display.get_surface()

        x, y = self.screen_shake_function(3)
    
    def rand_sin(self):
        amp = 1
        freq = randf(1, 5)
        return lambda x: amp * sin(freq * x)
    
    def screen_shake_function(self, degree):
        def summed_sine(x):
            result = 0
            for _ in range(degree):
                result += self.rand_sin()(x)
            dropoff = (2 * pi - x) / (2 * pi)
            return dropoff * result
        
        return (summed_sine, summed_sine)


window = Window()
with open(Path("config", "config.toml"), "rb") as f:
    config = toml.load(f)
    window.create_window(**config["window"])
