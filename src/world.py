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
        self.menu = menu

        # block data
        self.data = {}
        self.late_data = {}
        self.bg_data = {}
        self.chunk_surfaces = {}
        self.chunk_colors = {}

        # block lighting
        self.lightmap = {}
        self.light_surfaces = {}
        self.light_to_contrib = {}
        self.contrib_to_light = {}

        # world interactive stuff
        self.breaking = Breaking()

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
        r_squared = radius ** 2
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                dist_sq = dx*dx + dy*dy
                if dist_sq <= r_squared:
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
                blit_x, blit_y = rel_x * BS, rel_y * BS
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

                # update chunk data and blit block image
                if name != og_name:
                    self.set(chunk_index, block_pos, name)
    
    def get(self, chunk_index, block_pos):
        if chunk_index in self.data:
            return self.data[chunk_index].get(block_pos, None)
        return None
    
    def set(self, chunk_index, block_pos, name, propagate_light=True):
        """
        abstract set does 2 things:
        - modify the data
        - modify the lighting
        - propagate the lighting
        """
        # check whether block should be deleted or created
        if name == "air":
            if block_pos in self.data[chunk_index]:
                del self.data[chunk_index][block_pos]
        else:
            self.data[chunk_index][block_pos] = name

        if bwand(name, BF.EMPTY):
            if (chunk_index, block_pos) in self.light_to_contrib:
                # iterate through all blocks this light source has contributed towards
                for (con_chunk_index, con_block_pos) in self.light_to_contrib[(chunk_index, block_pos)]:
                    print((con_chunk_index, con_block_pos), (chunk_index, block_pos))
                    contribution = self.contrib_to_light[(con_chunk_index, con_block_pos)][(chunk_index, block_pos)]
                    self.update_lightmap(con_chunk_index, con_block_pos, contribution, decrease=True)

        # update lightmap when a light source is placed
        if bwand(name, BF.LIGHT_SOURCE):
            light = blocks.params[name]["light"]
            self.update_lightmap(chunk_index, block_pos, light)
        else:
            if block_pos not in self.lightmap[chunk_index]:
                self.update_lightmap(chunk_index, block_pos, 0)
                
        # update lighting texture
        if propagate_light:
            self.propagate_light(chunk_index, block_pos)
    
    def init_light(self, chunk_index):
        if chunk_index not in self.lightmap:
            self.lightmap[chunk_index] = {}
            self.light_surfaces[chunk_index] = pygame.Surface((CW * BS, CH * BS), pygame.SRCALPHA)
            self.light_to_contrib[chunk_index] = {}
    
    def create_chunk(self, chunk_index):
        # initialize new chunk data in the world datae
        chunk_x, chunk_y = chunk_index
        self.data[chunk_index] = {}
        self.chunk_colors[chunk_index] = [rand(0, 255) for _ in range(3)]
        self.bg_data[chunk_index] = {}
        self.init_light(chunk_index)

        # generate the chunk
        biome = Biome.FOREST
        for rel_y in range(CH):
            for rel_x in range(CW):
                # init variables
                blit_x, blit_y = rel_x * BS, rel_y * BS
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
                        name = "stone"
                        self.bg_data[chunk_index][(block_x, block_y)] = name | X.b

                elif chunk_y < 20:
                    # UNDERGROUND
                    name = "stone" | X.b if self.octave_noise(block_x, block_y, freq=0.04, octaves=3, lac=2) < 0.46 else "stone"
                    self.bg_data[chunk_index][(block_x, block_y)] = name | X.b
                
                else:
                    # DEPTH LIMIT
                    name = "blackstone"

                self.set(chunk_index, (block_x, block_y), name, propagate_light=False)

        self.modify_chunk(chunk_index)
        self.propagate_light(chunk_index)
    
    def propagate_light(self, chunk_index, block_pos=None):
        # initialize data structures
        queue = deque()
        light_sources = set()
        current_source = None

        # save all light sources
        for block_pos in (self.lightmap[chunk_index] if block_pos is None else (block_pos,)):
            light = self.lightmap[chunk_index][block_pos]
            if light > 0:
                queue.append((chunk_index, block_pos, light))
                light_sources.add((chunk_index, block_pos))

        # directions of propagation
        offsets = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        
        # work through the queue
        while queue:
            chunk_index, block_pos, desired_light = queue.popleft()

            # the current block is a light source
            if (chunk_index, block_pos) in light_sources:
                current_source = (chunk_index, block_pos)
                self.light_to_contrib[current_source] = {current_source}
                self.contrib_to_light[current_source] = {current_source: desired_light}

            for (xo, yo) in offsets:
                new_chunk_index, new_block_pos = self.correct_tile(chunk_index, block_pos, xo, yo)
                new_light = desired_light - 1

                # make sure that the lighting data (lightmap and -surface) of neighboring chunk is initialized
                self.init_light(new_chunk_index)

                # if the block doesn't exist yet, make it zero by default
                if new_block_pos not in self.lightmap[new_chunk_index]:
                    self.update_lightmap(new_chunk_index, new_block_pos, 0, )
                
                # if new lighting is higher than the lighting already there, overwrite it because this light source is brighter than its previous light source
                if new_light > self.lightmap[new_chunk_index][new_block_pos]:
                    if current_source is None:
                        self.update_lightmap(new_chunk_index, new_block_pos, new_light)
                    else:
                        self.update_lightmap(new_chunk_index, new_block_pos, new_light, current_source)
                    queue.append((new_chunk_index, new_block_pos, new_light))

    def update_lightmap(self, chunk_index, block_pos, light, src_key=None, decrease=False):
        # add this block to the contributions of the src_key and reverse
        if src_key is not None:
            # save light -> contribs
            con_key = (chunk_index, block_pos)
            if src_key not in self.light_to_contrib:
                self.light_to_contrib[src_key] = set()
            self.light_to_contrib[src_key].add(con_key)

            # save contrib -> lights
            cur_light = self.lightmap[chunk_index][block_pos]
            contribution = light - cur_light  # e.g. it was 3 but lit up to 7 so contribution is +4

            if con_key not in self.contrib_to_light:
                self.contrib_to_light[con_key] = {src_key: contribution}
            else:
                self.contrib_to_light[con_key][src_key] = contribution

        # update the map itself
        if decrease:
            self.lightmap[chunk_index][block_pos] -= light
        else:
            self.lightmap[chunk_index][block_pos] = light

        # update the pixel on the lightmap
        final_light_value = self.lightmap[chunk_index][block_pos]
        alpha = (MAX_LIGHT - final_light_value) / MAX_LIGHT * 255
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
                    block_x, block_y = block_pos
                    blit_pos = (block_x * BS - scroll[0], block_y * BS - scroll[1])

                    # process block modifications
                    base, mods = blocks.norm(name)
                    if "b" in mods:
                        image = blocks.images[base | X.b]
                    else:
                        image = blocks.images[base]

                    # ! render block !
                    display.blit(image, blit_pos)
                    
                    # add a block that can be interacted with
                    block_rects.append(pygame.Rect(*blit_pos, BS, BS))
                    num_blocks += 1

                # ! render lights !
                if self.menu.lighting:
                    display.blit(self.light_surfaces[chunk_index], chunk_rect)

                # debug lights
                if self.menu.debug_lighting:
                    for block_pos, name in self.lightmap[chunk_index].items():
                        key = (chunk_index, block_pos)
                        block_x, block_y = block_pos
                        blit_pos = (block_x * BS - scroll[0], block_y * BS - scroll[1])
                        write(window.display, "center", self.lightmap[chunk_index][block_pos], fonts.orbitron[12], pygame.Color("pink"), blit_pos[0] + BS / 2, blit_pos[1] + BS / 2)
                        if key in self.contrib_to_light:
                            write(window.display, "center", list(self.contrib_to_light[key].values())[0], fonts.orbitron[12], pygame.Color("yellow"), blit_pos[0] + BS / 2, blit_pos[1] + BS / 2)

                if self.menu.chunk_borders.checked:
                    pygame.draw.rect(display, self.chunk_colors[chunk_index], chunk_rect, 1)
                    write(display, "center", chunk_index, fonts.orbitron[20], WHITE, *chunk_rect.center)

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
