from appbase.decorators import fail_safe


def test_fail_safe():
    flag = False
    @fail_safe
    def add(a, b):
        if flag:
            # trying to raise exception
            1/0
        flag=True
        return a + b

    assert add(1, 2) == 3
    
    assert add(1, 2) == 3
