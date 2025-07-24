import pygame
from pathlib import Path
import tomllib as toml
from random import uniform as randf
from math import sin, pi
from pyengine.pgbasics import set_pyengine_gpu
from pygame._sdl2.video import Window, Renderer, Texture, Image
import pygame._sdl2.video
#
from pyengine.pgbasics import *
import pyengine.pgbasics as pgb
from pyengine.pgbasics import imgload as cpu_imgload


pygame.init()


class WindowHandler:
    def __init__(self, width, height, fullscreen, vsync, fps_cap, gpu):
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
        self.gpu = gpu
        self.center = (self.width / 2, self.height / 2)

        pygame.mouse.set_cursor(pygame.cursors.tri_left)

        if gpu:
            self.window = Window(size=self.size)
            self.display = Renderer(self.window, vsync=vsync)

            # GPU acceleration changes way loaded images and surfaces are created, modified and rendered
            set_pyengine_gpu(self.display)
        else:
            # pygame window and OpenGL flags
            pygame.display.set_caption("Blockingdom")
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
            pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, vsync)
            self.window = pygame.display.set_mode((self.width, self.height), 
            pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE,
                vsync=self.vsync
            )
            self.display = pygame.display.get_surface()
    
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


with open(Path("config", "config.toml"), "rb") as f:
    config = toml.load(f)
    window = WindowHandler(**config["window"])
