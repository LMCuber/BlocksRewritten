from .engine import *
from . import blocks
from .blocks import BF, bwand, nbwand


def modify_chunk( chunk_index):
    from .world import Biome, bio

    def _set(name, mod_pos):
        rel_x, rel_y = mod_pos[0] - chunk_index[0] * CW, mod_pos[1] - chunk_index[1] * CH
        if 0 <= rel_x < CW and 0 <= rel_y < CH:
            self.set(chunk_index, mod_pos, name, allow_propagation=False)
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
                    if not _spawned and chunk_index == (0, 0):
                        _spawned = True
                    if _chance(1 / 1) and not _spawned:
                        create_entity(
                            Transform(Vec2(0, 0), Vec2(0, 0), gravity=0, sines=[0, 5]),
                            Mob(MobType.NEUTRAL),
                            Hitbox((block_pos[0] * BS, block_pos[1] * BS - BS * 8), (0, 0), anchor="midbottom"),
                            Sprite.from_path(Path("res", "images", "mobs", "bee", "walk.png")),
                            Health(100),
                            Bee(),
                            NoJump(),
                            chunk=chunk_index
                        )
                        _spawned = True
                    
                    # create_entity(
                    #     Transform(Vec2(0, 0), Vec2(randf(0.1, 0.8), 0), gravity=0.03),
                    #     Mob(MobType.PASSIVE),
                    #     Hitbox((block_pos[0] * BS, block_pos[1] * BS - BS * 6), (30, 30), anchor="midbottom"),
                    #     Sprite.from_path(Path("res", "images", "mobs", "penguin", "walk.png")),
                    #     Health(100),
                    #     Loot({
                    #         "chicken": choice((1, 2))
                    #     }),
                    #     chunk=chunk_index
                    # )
                    
                    # poppy
                    if _chance(1 / 20):
                        if _chance(0.6):
                            poppy_color = "red"
                        else:
                            poppy_color = "yellow"
                        _set(f"{poppy_color}-poppy", (block_x, block_y - 1))

                    # forest tree
                    if _chance(1 / 24):
                        tree_height = _nordis(9, 2)
                        for tree_yo in range(tree_height):
                            wood_x, wood_y = block_x, block_y - tree_yo - 1 - 5
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
                bwand(name, BF.ORE)
                and _get((block_x, block_y - 1)) is not None and nbwand(_get((block_x, block_y - 1)), BF.ORE)
                and _get((block_x + 1, block_y)) is not None and nbwand(_get((block_x + 1, block_y)), BF.ORE)
                and _get((block_x, block_y + 1)) is not None and nbwand(_get((block_x, block_y + 1)), BF.ORE)
                and _get((block_x - 1, block_y)) is not None and nbwand(_get((block_x - 1, block_y)), BF.ORE)
            ):
                # ore vein is available to populate
                ore_x, ore_y = block_x, block_y
                for _ in range(_nordis(blocks.ores.veins.get(name, 4), 3)):
                    direc = _rand(0, 3)
                    if direc == 0: ore_x += 1
                    elif direc == 1: ore_x -= 1
                    elif direc == 2: ore_y += 1
                    elif direc == 3: ore_y -= 1
                    _set(name, (ore_x, ore_y))

            # update chunk data and blit block image
            if name != og_name:
                self.set(chunk_index, block_pos, name)
