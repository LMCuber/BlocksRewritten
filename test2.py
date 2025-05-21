from collections import deque
import time


CHUNK_SIZE = 16
MAX_LIGHT = 15

# Light and block maps
light_map = [[0 for _ in range(CHUNK_SIZE)] for _ in range(CHUNK_SIZE)]
blocks = [[0 for _ in range(CHUNK_SIZE)] for _ in range(CHUNK_SIZE)]

# Sample solid blocks
blocks[8][8] = 1  # solid block
blocks[4][6] = 1  # solid block

# Define light sources: (x, y, light_level)
light_sources = [
    (10, 5, 14),
]

# Falloff per tile: you can customize this later per tile type
def get_light_falloff(x, y):
    if blocks[y][x] == 1:
        return 2  # Solid block: stronger falloff
    else:
        return 1  # Air: normal falloff

# BFS queue
queue = deque()
for x, y, level in light_sources:
    queue.append((x, y, level))

# Directions (4-way for simplicity)
dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

while queue:
    x, y, light = queue.popleft()
    print(x, y, light, light_map[y][x])
    time.sleep(0.1)
    if not (0 <= x < CHUNK_SIZE and 0 <= y < CHUNK_SIZE):
        continue
    if light <= light_map[y][x]:
        continue

    light_map[y][x] = light

    for dx, dy in dirs:
        nx, ny = x + dx, y + dy
        if 0 <= nx < CHUNK_SIZE and 0 <= ny < CHUNK_SIZE:
            falloff = get_light_falloff(nx, ny)
            new_light = light - falloff
            if new_light > 0:
                queue.append((nx, ny, new_light))

# Print result
for row in light_map:
    continue
    print(" ".join(f"{cell:2}" for cell in row))