import opensimplex as osim
from enum import Enum
from collections import deque
import uuid
#
from pyengine.pgbasics import *
from pyengine.ecs import *
#
from .engine import *
from .window import *
from .entities import *
from .blocks import (
    BF, bwand, nbwand, MAX_LIGHT, X
)
from . import fonts
from . import blocks



# C L A S S E S
class Biome(Enum):
    FOREST = auto()
    MOUNTAIN = auto()
    BEACH = auto()


@dataclass
class BiomeData:
    blocks = {
        # cherry on top, main block, subblock
        Biome.FOREST: ("soil_f", "dirt_f"),
        Biome.MOUNTAIN: ("snow-stone", "stone"),
        Biome.BEACH: ("sand", "sand"),
    }


bio = BiomeData()


@dataclass
class Breaking:
    index: tuple[int, int] | None = None
    pos: tuple[int, int] | None = None
    anim: int = 0


class World:
    def __init__(self, menu):
        # params
        self.menu = menu

        # block data
        self.data = {}
        self.late_data = {}
        self.bg_data = {}
        self.chunk_surfaces = {}
        self.chunk_colors = {}

        # block lighting
        self.lightmap:           dict[Pos, dict[Pos, int]]                  = {} # light data
        self.light_surfaces:     dict[Pos, dict[Pos, pygame.Surface]]       = {} # light textures
        self.source_to_children: dict[Pos, dict[Pos, set[tuple[Pos, Pos]]]] = {} # saves all blocks that have been affected by a light source

        # world interactive stuff
        self.breaking = Breaking()

        # seed
        self.create_world()
        self.seed = uuid.uuid4().int
        osim.seed(self.seed)
        self.random = random.Random(self.seed)

        # misc
        self.lates = []
    
    @property
    def num_hor_chunks(self):
        """
        Quinn formule
        """
        return floor((window.width - 2) / (CW * BS)) + 2
    
    @property
    def num_ver_chunks(self):
        return floor((window.height - 2) / (CH * BS)) + 2
    
    def get_radius_around(self, radius):
        offsets = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                dist_sq = dx ** 2 + dy ** 2
                if dist_sq <= radius ** 2:
                    offsets.append((dist_sq, dx, dy))
        
        offsets.sort()
        
        return [(dx, dy) for _, dx, dy in offsets]
    
    def exists(self, chunk_index, block_pos):
        return chunk_index in self.data and block_pos in self.data[chunk_index]
    
    def break_(self, chunk_index, block_pos):
        """
        Abstract break does 1 thing:
        - Check whether block is breakable (blackstone is not)
        - Check whether the background block is air or can be fetched from bg_data
        """

        base, mods = blocks.norm(self.data[chunk_index][block_pos])

        if bwand(base, BF.UNBREAKABLE):
            return
        
        if "b" not in mods:
            if block_pos in self.bg_data[chunk_index]:
                self.set(chunk_index, block_pos, self.bg_data[chunk_index][block_pos])
            else:
                self.set(chunk_index, block_pos, "air")
    
    def get_blocks_around(self, rect, range_x=(-1, 1), range_y=(-1, 1), return_name=False):
        og_chunk_index, og_block_pos = self.pos_to_tile(rect.center)
        for yo in range(range_y[0], range_y[1] + 1):
            for xo in range(range_x[0], range_x[1] + 1):
                chunk_index, block_pos = self.correct_tile(og_chunk_index, og_block_pos, xo, yo)
                if chunk_index in self.data and block_pos in self.data[chunk_index]:
                    name = self.data[chunk_index][block_pos]
                    block_rect = pygame.Rect(block_pos[0] * BS, block_pos[1] * BS, BS, BS)
                    base, mods = blocks.norm(name)
                    if return_name:
                        yield (block_rect, base)
                    else:
                        if all(x not in mods for x in ["b", "B"]) and nbwand(base, BF.WALKABLE):
                            yield block_rect
    
    def screen_pos_to_tile(self, pos, scroll):
        x, y = pos
        # x and y must be unscaled and unscrolled; returns chunk and abs_pos ([chunk][pos] notation for accessation :D :P :/ :] Ü)
        target_x = floor(x / (BS * CW) + scroll[0] / (BS * CW))
        target_y = floor(y / (BS * CH) + scroll[1] / (BS * CH))
        target_chunk = (target_x, target_y)
        abs_x = floor(x / BS + scroll[0] / BS)
        abs_y = floor(y / BS + scroll[1] / BS)
        abs_pos = (abs_x, abs_y)
        return target_chunk, abs_pos

    def tile_to_screen_pos(self, abs_pos, scroll):
        abs_x, abs_y = abs_pos
        screen_x = (abs_x - scroll[0]) * BS
        screen_y = (abs_y - scroll[1]) * BS
        return screen_x, screen_y

    def pos_to_tile(self, pos):
        return ((
                floor(pos[0] / (CW * BS)),
                floor(pos[1] / (CH * BS)),
            ), (
                floor(pos[0] / BS),
                floor(pos[1] / BS),
            )
        )

    def correct_tile(self, chunk_index, block_pos, xo, yo):
        rel_x, rel_y = block_pos[0] % CW, block_pos[1] % CH
        default = True
        pos_xo = xo
        pos_yo = yo
        chunk_xo = chunk_yo = 0
        # correct (verb) (thanks didn't realizzze drizzo) bordering chunks
        if rel_x + xo < 0:
            chunk_xo -= 1
        elif rel_x + xo > CW - 1:
            chunk_xo += 1
        if rel_y + yo < 0:
            chunk_yo -= 1
        elif rel_y + yo > CH - 1:
            chunk_yo += 1
        block_pos = (block_pos[0] + pos_xo, block_pos[1] + pos_yo)
        chunk_index = (chunk_index[0] + chunk_xo, chunk_index[1] + chunk_yo)
        return chunk_index, block_pos

    def octave_noise(self, x, y, freq, amp=1, octaves=1, lac=2, pers=0.5):
        height = 0
        max_value = 0
        for i in range(octaves):
            nx = x * freq
            ny = y * freq
            height += amp * osim.noise2(x=nx, y=ny)

            max_value += amp
            freq *= lac
            amp *= pers

        height = (height + max_value) / (max_value * 2)
        return height

    def create_world(self):
        self.data = {}
    
    def modify_chunk(self, chunk_index):
        def _set(name, mod_pos):
            rel_x, rel_y = mod_pos[0] - chunk_index[0] * CW, mod_pos[1] - chunk_index[1] * CH
            if 0 <= rel_x < CW and 0 <= rel_y < CH:
                self.set(chunk_index, mod_pos, name)
            else:
                xo = mod_pos[0] - block_pos[0]
                yo = mod_pos[1] - block_pos[1]
                new_chunk_index, new_block_pos = self.correct_tile(chunk_index, block_pos, xo, yo)
                if new_chunk_index in self.late_data:
                    self.late_data[new_chunk_index][new_block_pos] = name
                else:
                    self.late_data[new_chunk_index] = {new_block_pos: name}
        
        def _get(mod_pos):
            rel_x, rel_y = mod_pos[0] - chunk_index[0] * CW, mod_pos[1] - chunk_index[1] * CH
            if 0 <= rel_x < CW and 0 <= rel_y < CH:
                try:
                    return self.data[chunk_index][mod_pos]
                except KeyError:
                    return "air"
            else:
                xo = mod_pos[0] - block_pos[0]
                yo = mod_pos[1] - block_pos[1]
                new_chunk_index, new_block_pos = self.correct_tile(chunk_index, block_pos, xo, yo)
                try:
                    return self.data[new_chunk_index][new_block_pos]
                except KeyError:
                    return None

        _chance = lambda p: self.random.random() < p
        _rand = lambda a, b: self.random.randint(a, b)
        _nordis = lambda mu, sigma: int(self.random.gauss(mu, sigma))
        _choice = lambda x: self.random.choice(x)

        biome = Biome.FOREST

        chunk_x, chunk_y = chunk_index
        _spawned = False
        for rel_y in range(CH):
            for rel_x in range(CW):
                # init
                block_pos = block_x, block_y = chunk_x * CW + rel_x, chunk_y * CH + rel_y
                name = og_name = self.data[chunk_index].get(block_pos, None)

                # topmost block (soil or something)
                if name == bio.blocks[biome][0] and _get((block_x, block_y - 1)) == "air":
                    # forest modifications
                    if biome == Biome.FOREST:
                        # entitites
                        if not _spawned and False and chunk_index == (0, 0) and _chance(1 / 5):
                            create_entity(
                                Transform([0, 0], [2.1, 0], flag=TransformFlag(TransformFlags.MOB), gravity=0.03),
                                Hitbox((block_pos[0] * BS, block_pos[1] * BS - BS * 6), (0, 0), anchor="midbottom"),
                                Sprite.from_path(Path("res", "images", "mobs", "bok-bok", "walk.png")),
                                PlayerFollower(0),
                                Headbutter(30),
                                chunk=chunk_index
                            )
                            _spawned = True
                        if _chance(1 / 20):
                            create_entity(
                                Transform([0, 0], [0, 0], gravity=0.08),
                                Hitbox((block_pos[0] * BS, block_pos[1] * BS - BS * 6), (100, 100), anchor="midbottom"),
                                Sprite.from_path(Path("res", "images", "spritesheets", "statics", "portal", "idle.png")),
                                chunk=chunk_index
                            )
                        # forest tree
                        if _chance(1 / 24):
                            # tree_height = _rand(10, 14)
                            tree_height = _nordis(9, 2)
                            for tree_yo in range(tree_height):
                                wood_x, wood_y = block_x, block_y - tree_yo - 1
                                wood_suffix = ""
                                leaf_name = "leaf_f"
                                leaf_chance = 1 / 2.4
                                if tree_yo > 0:
                                    if _chance(leaf_chance):
                                        wood_suffix += "L"
                                        _set(leaf_name, (wood_x - 1, wood_y))
                                    if _chance(leaf_chance):
                                        wood_suffix += "R"
                                        _set(leaf_name, (wood_x + 1, wood_y))
                                    if tree_yo == tree_height - 1:
                                        wood_suffix += "T"
                                        _set(leaf_name, (wood_x, wood_y - 1))
                                wood_suffix = "N" if not wood_suffix else wood_suffix
                                wood_name = f"wood_f_vr{wood_suffix}"
                                _set(wood_name, (wood_x, wood_y))
                    
                    elif biome == Biome.BEACH:
                        # rock
                        if _chance(1 / 15):
                            _set("rock" | X.b, (block_x, block_y - 1))

                        # beach tree
                        if _chance(1 / 24):
                            # tree stem
                            tree_height = _nordis(9, 2)
                            for tree_yo in range(tree_height):
                                wood_x, wood_y = block_x, block_y - tree_yo - 1
                                _set("wood_p", (wood_x, wood_y))
                            leaf_x, leaf_y = wood_x, wood_y
                            # trees
                            _set("leaf_f", (wood_x - 1, wood_y))
                            _set("leaf_f", (wood_x, wood_y - 1))
                            _set("leaf_f", (wood_x + 1, wood_y))
                
                # populate the ore veins
                if (
                    name == "base-ore"
                    and _get((block_x, block_y - 1)) != "base-ore"
                    and _get((block_x + 1, block_y)) != "base-ore"
                    and _get((block_x, block_y + 1)) != "base-ore"
                    and _get((block_x - 1, block_y)) != "base-ore"
                ):
                    ore_x, ore_y = block_x, block_y
                    for _ in range(_nordis(blocks.ores.veins["base-ore"], 3)):
                        direc = _rand(0, 3)
                        if direc == 0: ore_x += 1
                        elif direc == 1: ore_x -= 1
                        elif direc == 2: ore_y += 1
                        elif direc == 3: ore_y -= 1
                        if _get((ore_x, ore_y)) == "stone":
                            _set("base-ore", (ore_x, ore_y))

                # update chunk data and blit block image
                if name != og_name:
                    self.set(chunk_index, block_pos, name)
    
    def get(self, chunk_index, block_pos):
        if chunk_index in self.data:
            return self.data[chunk_index].get(block_pos, None)
        return None
    
    def set(self, chunk_index, block_pos, name, propagate_light=True):
        """
        does 3 things:
        - modify the data
        - modify the lighting
        - propagate the lighting
        """
        if block_pos in self.data[chunk_index]:
            cur = self.data[chunk_index][block_pos]

            # deleting a light source (depropagate)
            if bwand(cur, BF.LIGHT_SOURCE):
                if chunk_index in self.source_to_children and self.source_to_children[chunk_index].get(block_pos, False):
                    light_shares: dict[tuple[Pos, Pos], int] = {}

                    # for all light children, check the distance to all other light sources
                    for child_chunk_index, child_block_pos in self.source_to_children[chunk_index][block_pos]:
                        for yo in range(-1, 2):
                            for xo in range(-1, 2):
                                nei_chunk_index = (chunk_index[0] + xo, chunk_index[1] + yo)
                                if nei_chunk_index not in self.data:
                                    self.create_chunk(nei_chunk_index)
                                
                                for nei_light_block_pos in self.source_to_children[nei_chunk_index]:
                                    if (nei_chunk_index, nei_light_block_pos) != (chunk_index, block_pos):
                                        nei_light_name = self.data[nei_chunk_index][nei_light_block_pos]
                                        light_power = blocks.params[nei_light_name]["light"]
                                        dist = abs(nei_light_block_pos[0] - child_block_pos[0]) + abs(nei_light_block_pos[1] - child_block_pos[1])
                                        light_value_from_other_source = light_power - dist * blocks.params[nei_light_name].get("light_falloff", 1)
                                        light_shares[(nei_chunk_index, nei_light_block_pos)] = light_value_from_other_source
                        
                        # check if there are light sources in the vicinity
                        if light_shares:
                            # save the source that illuminates the given block the most
                            max_light_key = max(light_shares, key=light_shares.get)
                            max_light_value = light_shares[max_light_key]
                            if max_light_value > 0:
                                self.update_lightmap(child_chunk_index, child_block_pos, max_light_value)
                                # transfer this child the other light source's child, because it has taken over it
                                self.source_to_children[max_light_key[0]][max_light_key[1]].add((child_chunk_index, child_block_pos))
                            else:
                                self.update_lightmap(child_chunk_index, child_block_pos, 0)
                        else:
                            # the block can't possibly be shared by any other light sources, so it just becomes black
                            self.update_lightmap(child_chunk_index, child_block_pos, 0)

                    del self.source_to_children[chunk_index][block_pos]
                    propagate_light = False
                 
        self.data[chunk_index][block_pos] = name

        if bwand(name, BF.LIGHT_SOURCE):
            # update lightmap when a light source is placed
            light = blocks.params[name]["light"]

            self.update_lightmap(chunk_index, block_pos, light)
        else:
            if block_pos not in self.lightmap[chunk_index]:
                self.update_lightmap(chunk_index, block_pos, 0)
        
        # update chunk surface
        base, mods = blocks.norm(name)
        if "b" in mods:
            image = blocks.images[base | X.b]
        else:
            image = blocks.images[base]
        self.chunk_surfaces[chunk_index].blit(image, (block_pos[0] % CW * BS, block_pos[1] % CH * BS))
                
        # update lighting surface
        if propagate_light:
            self.propagate_light(chunk_index, block_pos)
    
    def init_light(self, chunk_index):
        if chunk_index not in self.lightmap:
            self.lightmap[chunk_index] = {}
            self.light_surfaces[chunk_index] = pygame.Surface((CW * BS, CH * BS), pygame.SRCALPHA)
            self.source_to_children[chunk_index] = {}
    
    def create_chunk(self, chunk_index):
        # initialize new chunk data in the world datae
        chunk_x, chunk_y = chunk_index
        self.data[chunk_index] = {}
        self.chunk_surfaces[chunk_index] = pygame.Surface((CW * BS, CH * BS), pygame.SRCALPHA)
        self.chunk_colors[chunk_index] = [rand(0, 255) for _ in range(3)]
        self.bg_data[chunk_index] = {}
        self.init_light(chunk_index)

        # generate the chunk
        biome = Biome.FOREST
        for rel_y in range(CH):
            for rel_x in range(CW):
                # init variables
                block_x, block_y = chunk_x * CW + rel_x, chunk_y * CH + rel_y

                # chunks 0 and 1 need 1D noise for terrain height
                if chunk_y in (0, 1):
                    offset = int(self.octave_noise(block_x, 0, 0.04) * CW)

                if chunk_y < 0:
                    # SKY
                    name = "air"

                elif chunk_y == 0:
                    # GROUND LEVEL
                    if rel_y == offset:
                        # top block in a biome
                        name = bio.blocks[biome][0]
                        if name == "soil_f":
                            self.bg_data[chunk_index][(block_x, block_y)] = "dirt_f" | X.b
                        else:
                            self.bg_data[chunk_index][(block_x, block_y)] = name | X.b
                    elif rel_y < offset:
                        # air
                        name = "air"
                    else:
                        # underground blocks
                        name = bio.blocks[biome][1]
                        self.bg_data[chunk_index][(block_x, block_y)] = name | X.b

                elif chunk_y == 1:
                    # DIRT-CAVE HYBRID
                    if rel_y <= offset:
                        name = bio.blocks[biome][1]
                        self.bg_data[chunk_index][(block_x, block_y)] = name | X.b
                    else:
                        name = self.get_ore(block_y)
                        self.bg_data[chunk_index][(block_x, block_y)] = name | X.b

                elif chunk_y < 20:
                    # UNDERGROUND
                    name = "stone" | X.b if self.octave_noise(block_x, block_y, freq=0.04, octaves=3, lac=2) < 0.46 else self.get_ore(block_y)
                    self.bg_data[chunk_index][(block_x, block_y)] = name | X.b
                else:
                    # DEPTH LIMIT
                    name = "blackstone"

                self.set(chunk_index, (block_x, block_y), name, propagate_light=False)

        self.modify_chunk(chunk_index)
        self.propagate_light(chunk_index)
    
    def get_ore(self, depth):
        if self.random.randint(0, 100) == 0:
            return "base-ore"
        return "stone"
    
    def propagate_light(self, chunk_index, block_pos=None):
        # initialize data structures
        queue = deque()
        light_sources = set()

        # save all light sources
        for block_pos in (self.lightmap[chunk_index] if block_pos is None else (block_pos,)):
            if block_pos not in self.data[chunk_index]:
                continue
            name = self.data[chunk_index][block_pos]
            if bwand(name, BF.LIGHT_SOURCE):
                light = blocks.params[name]["light"]
                queue.append((chunk_index, block_pos, light))
                light_sources.add((chunk_index, block_pos))
                self.update_lightmap(chunk_index, block_pos, light)

        # directions of propagation
        offsets = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        n = 0
        
        # work through the queue
        while queue:
            n += 1
            chunk_index, block_pos, desired_light = queue.popleft()

            # check if the current block is a light source
            if (chunk_index, block_pos) in light_sources:
                current_source = (chunk_index, block_pos)
                if current_source[0] not in self.source_to_children:
                    self.source_to_children[current_source[0]] = {}
                self.source_to_children[current_source[0]][current_source[1]] = {current_source}

            for (xo, yo) in offsets:
                new_chunk_index, new_block_pos = self.correct_tile(chunk_index, block_pos, xo, yo)
                new_light = desired_light - blocks.params[self.data[current_source[0]][current_source[1]]].get("light_falloff", 1)

                # make sure that the lighting data (lightmap and -surface) of neighboring chunk is initialized
                self.init_light(new_chunk_index)

                # if the block doesn't exist yet, make it zero by default
                if new_block_pos not in self.lightmap[new_chunk_index]:
                    self.update_lightmap(new_chunk_index, new_block_pos, 0)

                # return if light becomes too dim
                if new_light < 0:
                    continue

                # if new lighting is higher than the lighting already there, overwrite it because this light source is brighter than its previous light source
                if new_light > self.lightmap[new_chunk_index][new_block_pos]:
                    self.update_lightmap(new_chunk_index, new_block_pos, new_light, src_key=current_source)
                    queue.append((new_chunk_index, new_block_pos, new_light))

    def update_lightmap(self, chunk_index, block_pos, light, src_key=None):
        # add this block to the contributions (children) of the src_key
        if src_key is not None:
            child_key = (chunk_index, block_pos)
            self.source_to_children[src_key[0]][src_key[1]].add(child_key)

        self.lightmap[chunk_index][block_pos] = light

        # update the pixel on the lightmap
        final_light_value = self.lightmap[chunk_index][block_pos]
        alpha = (MAX_LIGHT - final_light_value) / MAX_LIGHT * 255
        alpha = clamp(alpha, 0, 255)
        blit_pos = (block_pos[0] % CW * BS, block_pos[1] % CH * BS)
        pygame.draw.rect(self.light_surfaces[chunk_index], (0, 0, 0, alpha), (*blit_pos, BS, BS))

    def update(self, display, scroll):
        # lates
        for pos in self.lates:
            pygame.draw.aacircle(display, RED, pos, 3)

        # actual
        num_blocks = 0
        processed_chunks = []
        block_rects = []

        # clear the lightmap
        # self.lightmap.fill(BLACK)
        for yo in range(self.num_ver_chunks):
            for xo in range(self.num_hor_chunks):
                # get chunk coordinates from game scroll
                chunk_x = xo - 1 + int(round(scroll[0] / (CW * BS)))
                chunk_y = yo - 1 + int(round(scroll[1] / (CH * BS)))
                chunk_index = (chunk_x, chunk_y)

                # create chunk in case it does not exist yet
                if chunk_index not in self.data:
                    self.create_chunk(chunk_index)

                # check whether it is just late
                if chunk_index in self.late_data:
                    for block_pos, name in self.late_data[chunk_index].copy().items():
                        self.set(chunk_index, block_pos, name)
                        del self.late_data[chunk_index][block_pos]

                # render the shunk surface
                chunk_topleft = chunk_index[0] * CW * BS - scroll[0], chunk_index[1] * CH * BS - scroll[1]
                chunk_rect = pygame.Rect((*chunk_topleft, CW * BS, CH * BS))

                for block_pos, name in self.data[chunk_index].items():
                    num_blocks += 1

                    continue

                    block_x, block_y = block_pos
                    blit_pos = (block_x * BS - scroll[0], block_y * BS - scroll[1])
                    
                    # add a block that can be interacted with
                    block_rects.append(pygame.Rect(*blit_pos, BS, BS))

                # ! render chunk surface !
                display.blit(self.chunk_surfaces[chunk_index], chunk_rect)

                # ! render lights !
                if self.menu.lighting:
                    display.blit(self.light_surfaces[chunk_index], chunk_rect)

                # debug stuff per block
                if self.menu.debug_lighting:
                    for block_pos, name in self.lightmap[chunk_index].items():
                        key = (chunk_index, block_pos)
                        block_x, block_y = block_pos
                        blit_pos = (block_x * BS - scroll[0], block_y * BS - scroll[1])
                        write(window.display, "center", self.lightmap[chunk_index][block_pos], fonts.orbitron[12], pygame.Color("orange"), blit_pos[0] + BS / 2, blit_pos[1] + BS / 2)

                if self.menu.chunk_borders.checked:
                    pygame.draw.rect(display, self.chunk_colors[chunk_index], chunk_rect, 1)
                    write(display, "center", chunk_index, fonts.orbitron[20], WHITE, *chunk_rect.center)
                    write(display, "center", (chunk_index[0] * CW, chunk_index[1] * CH), fonts.orbitron[12], WHITE, chunk_rect.centerx, chunk_rect.centery + 30)

                processed_chunks.append(chunk_index)

        # show the breaking block
        if (self.breaking.index, self.breaking.pos) != (None, None):
            breaking_pos = (self.breaking.pos[0] * BS - scroll[0], self.breaking.pos[1] * BS - scroll[1])
            # check if the breaking actually breaks
            try:
                blocks.breaking_sprs[int(self.breaking.anim)]
            except IndexError:
                # drop the item
                self.drop()
                # break the block
                self.break_(self.breaking.index, self.breaking.pos)
                # reset the breaking
                self.breaking.index = None
                self.breaking.pos = None
            else:
                # render the block breaking spritesheet
                display.blit(blocks.breaking_sprs[int(self.breaking.anim)], breaking_pos)

        # return information
        return num_blocks, processed_chunks, block_rects

    def drop(self):
        # coordinates for the drop
        x = self.breaking.pos[0] * BS + BS / 2
        y = self.breaking.pos[1] * BS + BS / 2
        # block image
        base, _ = blocks.norm(self.data[self.breaking.index][self.breaking.pos])
        # modify the dropped image so it distinguished itself form its environment
        drop_img = pygame.transform.scale_by(blocks.images[base], 0.5)
        if not (bwand(base, BF.NONSQUARE)):
            pygame.draw.rect(drop_img, BLACK, (0, 0, *drop_img.size), 1)
        #
        # create_entity(
        #     Transform([x - BS / 4 + rand(-5, 5), y - BS / 4 + rand(-5, 5)], [0, 0], gravity=0.03, sine=(0.35, 4)),
        #     Sprite.from_img(drop_img),
        #     Drop(base),
        #     chunk=0
        # )
