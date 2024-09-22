import unittest
from dataclasses import dataclass
from block_scoping import block_scoping, BlockScopingException

class TestBlockScoping(unittest.TestCase):

    
    def test_for_type_hint1(self):
        @block_scoping
        def f():
            i: int
            if True:
                i = 3
            print(i)

    def test_for_type_hint2(self):
        @block_scoping
        def f():
            i: list = [1, 2, 3]
            print(i)

    def test_for_type_hint3(self):
        @block_scoping
        def f(i : int):
            print(i)

if __name__ == '__main__':
    unittest.main(verbosity=2)