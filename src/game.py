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
from src.tools import *
from src import world
from src import player
from src import fonts
from src import joystick
from src import menu


class Game:
    def __init__(self):
        # initialization stuff
        self.widget_kwargs = {"font": fonts.orbitron[20], "anchor": "topleft"}
        self.clock = pygame.time.Clock()
        self.init_systems()
        self.shader = ModernglShader(Path("src", "shaders", "vertex.glsl"), Path("src", "shaders", "fragment.glsl"))
        # runtime objects
        self.world = world.World(menu)
        self.player = player.Player(self, self.world, menu)
        self.fake_scroll = [0, 0]
        self.scroll = [0, 0]
        self.last_start = ticks()
        self.state = States.PLAY
        self.substate = Substates.PLAY
        # joystick
        self.joystick = joystick.JoystickManager()
        #
        self.sword = get_sword((120, 120, 120))
        # menu stuff
        menu.quit_button.command = self.quit
    
    @staticmethod
    def quit(self):
        self.running = False
    
    def init_systems(self):
        self.render_system = RenderSystem(window.display)
        self.player_follower_system = PlayerFollowerSystem(window.display)
        self.debug_system = DebugSystem(window.display)
        self.collision_system = CollisionSystem()
        self.display_health_system = DisplayHealthSystem(window.display)
        self.drop_system = DropSystem(window.display)
    
    def process_systems(self, processed_chunks):
        self.render_system.process(self.scroll, self.world, menu.hitboxes, chunks=processed_chunks)
        self.player_follower_system.process(self.player, chunks=processed_chunks)
        self.collision_system.process(self.player, chunks=processed_chunks)
        self.display_health_system.process(self.scroll, chunks=processed_chunks)
        self.drop_system.process(self.player, self.scroll, chunks=processed_chunks)
    
    def send_data_to_shader(self):
        # send textures to the shader
        self.shader.send_surf(0, "tex", window.display)
        self.shader.send_surf(1, "paletteTex", blocks.palette_img)

        # send uniform data to the shader
        self.shader.send("pink", [c / 255 for c in PINK_RED[:3]])
        self.shader.send("time", ticks())
        # self.shader.send("centerWin", window.center)
        self.shader.send("res", (window.width, window.height))

        w = 120
        # self.shader.send("deadZone", (pygame.mouse.get_pos()[0] - w, pygame.mouse.get_pos()[1] - w, w * 2, w * 2))
        # self.shader.send("deadZone", (window.width / 2 - w, window.height / 2 - w, w * 2, w * 2))
        self.shader.send("deadZone", (0, 0, 0, 0))
        o = 0
        self.shader.send("rOffset", (-o, 0))
        self.shader.send("gOffset", (0, 0))
        self.shader.send("bOffset", (o, 0))

        self.shader.send("grayscale", self.substate == Substates.MENU)

        # self.shader.send("lightPosWin", self.player.rect.move(-self.scroll[0], -self.scroll[1]).center)
        # self.shader.send("lightPowerWin", 0)

    def apply_scroll(self, m):
        self.fake_scroll[0] += (self.player.rect.x - self.fake_scroll[0] - window.width / 2 + self.player.rect.width / 2) * m
        self.fake_scroll[1] += (self.player.rect.y - self.fake_scroll[1] - window.height / 2 + self.player.rect.height / 2) * m
        self.scroll[0] = int(self.fake_scroll[0])
        self.scroll[1] = int(self.fake_scroll[1])
    
    def quit(self):
        pygame.quit()
        sys.exit()
            
    def mainloop(self):
        self.running = True
        while self.running:
            window.target_fps = menu.target_fps.value
            dt = self.clock.tick(165) / (1 / 144 * 1000)

            for event in pygame.event.get():
                pgw.process_widget_events(event)
                self.player.process_event(event)

                if event.type == pygame.QUIT:
                    self.quit()
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == States.PLAY:
                            if self.substate == Substates.PLAY:
                                self.substate = Substates.MENU
                                for widget in menu.widgets:
                                    widget.enable()
                            elif self.substate == Substates.MENU:
                                self.substate = Substates.PLAY
                                for widget in menu.widgets:
                                    widget.disable()
                    
                    elif event.key == pygame.K_q:
                        self.running = False
                
                elif event.type == pygame.VIDEORESIZE:
                    print(event.size)
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pass

            window.display.fill(SKY_BLUE)

            # scroll the display
            self.apply_scroll(0.1)

            # -------- P L A Y ---------------------------
            if self.state == States.PLAY:
                # draw and update the terrain
                num_blocks, processed_chunks, block_rects = self.world.update(window.display, self.scroll)
                processed_chunks.append(0)  # the "global" chunk, so entities that update always

                # update the player
                self.player.update(window.display, block_rects, dt)

                # process the ECS systems   
                self.process_systems(processed_chunks)

            # update the pyengine.pgwidgets
            pgw.draw_and_update_widgets()

            # display the fps
            write(window.display, "topleft", f"FPS : {int(self.clock.get_fps())}", fonts.orbitron[20], BLACK, 5, 5)
            if window.vsync:
                write(window.display, "topleft", "vsync", fonts.orbitron[10], BLACK, 5, 24)
            write(window.display, "topleft", f"blocks : {num_blocks}", fonts.orbitron[15], BLACK, 5, 40)
            # write(window.display, "topleft", f"chunks : {len(processed_chunks)} -> {processed_chunks}", fonts.orbitron[15], BLACK, 5, 60)
            write(window.display, "topleft", f"State: {self.state}", fonts.orbitron[15], BLACK, 5, 80)
            write(window.display, "topleft", f"Substate: {self.substate}", fonts.orbitron[15], BLACK, 5, 100)

            # --- DO RENDERING BEFORE THIS BLOCK ---
            self.send_data_to_shader()

            # render the shader
            self.shader.render()

            # window.window.flip()
            pygame.display.flip()

            self.shader.release_all_textures()

            # if ticks() - self.last_start >= 5_000:
            #     self.running = False

        self.quit()
