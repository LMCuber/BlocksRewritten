import pygame
from pathlib import Path
import sys
#
from pyengine.pgshaders import *
from pyengine.pgbasics import *
import pyengine.pgwidgets as pgw
#
from src.window import *
from src.entities import *
from src.tools import *
from src.midblit import Midblit
from src import world
from src import player
from src import fonts
from src import joystick
from src import menu


class Game:
    def __init__(self, config):
        # parse the config first
        self.config = config
        # rendering and frames
        self.clock = pygame.time.Clock()
        if not window.gpu:
            self.shader = ModernglShader(
                Path("src", "shaders", "default.vert"),
                Path("src", "shaders", "default.frag")
            )
        self.dead_zone = None
        # runtime objects
        self.world = world.World(menu, **self.config["world"])
        self.player = player.Player(self, self.world, menu)
        self.fake_scroll = [0, 0]
        self.scroll = [0, 0]
        self.last_start = ticks()
        self.last_frame = ticks()
        self.state = States.PLAY
        self.substate = Substates.PLAY
        self.disable_input = False
        self.num_rendered_entities = 0
        self.num_frames = 0
        self.dt = 1
        # joystick
        self.joystick = joystick.JoystickManager()
        # UI / UX
        self.sword = get_rock((120, 120, 120))
        # self.sword = get_axe((120, 120, 120))
        self.midblit = Midblit(self, window)
        # menu stuff
        menu.quit.command = self.quit
        # systems
        self.init_systems()
    
    @property
    def stat_color(self):
        return BLACK if self.scroll[1] < 220 else WHITE
    
    def init_systems(self):
        self.chunk_repositioning_system = ChunkRepositioningSystem()
        self.render_system = RenderSystem(window.display)
        self.physics_system = PhysicsSystem(window.display, self.world)
        self.player_follower_system = PlayerFollowerSystem(window.display, self.player)
        # self.debug_system = DebugSystem(window.display)
        self.mob_system = MobSystem()
        self.collision_player_entity_system = CollisionPlayerEntitySystem(self.player)
        self.damage_text_system = DamageTextSystem(window.display)
        self.health_display_system = HealthDisplaySystem(window.display)
        self.drop_system = DropSystem(window.display, self.player)
    
    def process_systems(self, processed_chunks):
        # Render system gets processed at world.py
        self.chunk_repositioning_system    .process(chunks=processed_chunks)
        self.physics_system                .process(self.scroll, menu.hitboxes, menu.collisions, self.dt, chunks=processed_chunks)
        self.player_follower_system        .process(chunks=processed_chunks)
        self.mob_system                    .process(chunks=processed_chunks)
        self.collision_player_entity_system.process(chunks=processed_chunks)
        self.drop_system                   .process(chunks=processed_chunks)
        self.health_display_system         .process(self.scroll, chunks=processed_chunks)
    
    def send_data_to_shader(self):
        # send textures to the shader
        self.shader.send_surf(0, "tex", window.display)
        # self.shader.send_surf(1, "lightmap", self.world.lightmap)
        self.shader.send_surf(2, "paletteTex", blocks.palette_img)

        # send uniform data to the shader
        self.shader.send("pink", [c / 255 for c in PINK_RED[:3]])
        self.shader.send("time", ticks())
        # self.shader.send("centerWin", window.center)
        self.shader.send("res", (window.width, window.height))
        self.shader.send("palettize", menu.palettize.checked)

        w = 120
        if self.midblit.active:
            self.dead_zone = self.midblit.rect
        else:
            self.dead_zone = (0, 0, 0, 0)
        self.shader.send("deadZone", self.dead_zone)
        o = 0
        self.shader.send("rOffset", (-o, 0))
        self.shader.send("gOffset", (0, 0))
        self.shader.send("bOffset", (o, 0))

        self.shader.send("grayscale", self.substate == Substates.MENU)

    def apply_scroll(self, m):
        self.fake_scroll[0] += (self.player.rect.x - self.fake_scroll[0] - window.width / 2 + self.player.rect.width / 2) * m
        self.fake_scroll[1] += (self.player.rect.y - self.fake_scroll[1] - window.height / 2 + self.player.rect.height / 2) * m
        self.scroll[0] = int(self.fake_scroll[0])
        self.scroll[1] = int(self.fake_scroll[1])
    
    def quit(self, timer_msg=False):
        elapsed = ticks() - self.last_start
        if timer_msg:
            print(Fore.GREEN
                  + f"""
Runtime: 
- {elapsed / 1000:.3f}s
- {self.num_frames} frames
- avg. FPS: {self.num_frames / elapsed * 1000:.3f}
                  """)
        pygame.quit()
        sys.exit()
            
    def mainloop(self):
        self.running = True
        while self.running:
            self.last_frame = ticks()
            self.num_frames += 1
            window.fps_cap = menu.fps_cap.value

            for event in pygame.event.get():
                pgw.process_widget_events(event)
                self.midblit.process_event(event)
                self.player.process_event(event)

                if event.type == pygame.QUIT:
                    self.quit()
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == States.PLAY:
                            if self.substate == Substates.PLAY:
                                self.substate = Substates.MENU
                                for widget in menu.iter_widgets():
                                    widget.enable()
                            elif self.substate == Substates.MENU:
                                self.substate = Substates.PLAY
                                for widget in menu.iter_widgets():
                                    widget.disable()
                    
                    elif event.key == pygame.K_SPACE:
                        pprint(self.world.wall_data[(0, 2)])
                        raise
                    
                    elif event.key == pygame.K_q:
                        self.quit()
                
                elif event.type == pygame.VIDEORESIZE:
                    print(event.size)
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pass

            pgb.fill_display(window.display, SKY_BLUE)

            # scroll the display
            self.apply_scroll(0.1)

            # -------- P L A Y ---------------------------
            num_blocks = 0
            if self.state == States.PLAY:
                # draw and update the terrain
                self.num_rendered_entities = 0
                num_blocks, processed_chunks, block_rects = self.world.update(window.display, self.scroll, self, self.dt)
                
                # process the ECS systems
                self.process_systems(processed_chunks)

                # inventory
                self.player.inventory.update(window.display)

                # midblit
                self.midblit.update()

            # update the pyengine.pgwidgets
            pgw.draw_and_update_widgets()

            # display the fps
            pgb.write(window.display, "topleft", f"FPS : {int(self.clock.get_fps())}", fonts.orbitron[20], self.stat_color, 5, 5)

            # display important parameters
            params = "params:\n"
            if self.config["game"]["profile"]:
                params += f"{EMD} profiled\n"
            if window.vsync:
                params += f"{EMD} vsync\n"
            params += f"{EMD} {("GPU" if window.gpu else "CPU")}\n"
            params += f"{EMD} {("cached chunks" if self.world.cache_chunk_textures else "iterated chunks")}\n"
            if self.world.lighting:
                params += f"{EMD} {("cached lighting" if self.world.cache_chunk_textures else "iterated lighting")}\n"
            else:
                params += f"{EMD} {"no lighting"}\n"
            params = params.removesuffix("\n")
            if params:
                pgb.write(window.display, "topleft", params, fonts.orbitron[12], self.stat_color, 5, 30)

            # display debugging / performance stats
            pgb.write(window.display, "topleft", f"blocks : {num_blocks} ({self.world.num_hor_chunks} x {self.world.num_ver_chunks} chunks)", fonts.orbitron[15], self.stat_color, 5, 110)
            pgb.write(window.display, "topleft", f"entities : {self.num_rendered_entities}", fonts.orbitron[15], self.stat_color, 5, 130)
            pgb.write(window.display, "topleft", f"State: {self.state}", fonts.orbitron[15], self.stat_color, 5, 150)
            pgb.write(window.display, "topleft", f"Substate: {self.substate}", fonts.orbitron[15], self.stat_color, 5, 170)

            # --- DO ALL RENDERING BEFORE THIS CODE BELOW ---
            if not window.gpu:
                # send relevant uniform data to the shader
                self.send_data_to_shader()

                # render the shader
                self.shader.render()

            # refreshes the window so you can see it
            if window.gpu:
                window.display.present()
            else:
                pygame.display.flip()

            # you shant guess what this function does
            if not window.gpu:
                self.shader.release_all_textures()

            # debug quit
            if ticks() - self.last_start >= self.config["game"].get("timer", float("inf")):
                self.quit(timer_msg=True)
            
            # cap fps
            self.dt = self.clock.tick() / (1 / 165 * 1000) # normalized dt; 1 when perfectly stable
            if self.dt > 10:
                self.dt = 10

        self.quit()
