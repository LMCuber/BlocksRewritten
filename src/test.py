def wrapper(cls):
    og_init = cls.__init__

    def __init__(self, *args, **kwargs):
        print("2 first")
        og_init(self, *args, **kwargs)



    cls.__init__ = __init__
    return cls


@wrapper
class Foo:
    def __init__(self, n):
        print("my bumber is:" + str(n))
    


foo = Foo(10)