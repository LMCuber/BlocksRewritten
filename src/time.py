import timeit
import random


class Foo:
    def __init__(self):
        self.choices = [random.random() for _ in range(random.randint(1, 50))]
        self.len = len(self.choices)


def cmin():
    min_tile = None
    min_len = float('inf')

    for tile in asd:
        l = tile.len
        if l < min_len:
            min_len = l
            min_tile = tile
    return min_tile


asd = [Foo() for _ in range(200)]

# print(timeit.timeit("min(asd, key=lambda x: len(x.choices))", globals=globals()))
print(timeit.timeit("cmin()", globals=globals()))