import random

from appbase.decorators import failsafe

c = 0

def test_failsafe():
    global c
    @failsafe
    def add(a, b):
        global c
        print(c)
        if c and c % 2:
            c += 1
            print('F')
            # trying to raise exception
            1/0
        return a + b

    for i in range(9):
        assert add(1, 2) == 3
        assert add(1, 7) == 8
        assert add(1, b=3) == 4
        c += 1
