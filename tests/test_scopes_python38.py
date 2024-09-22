import unittest
from dataclasses import dataclass
from block_scoping import block_scoping, BlockScopingException

class TestBlockScoping(unittest.TestCase):

    
    def test_if_walrus_1(self):
        @block_scoping
        def f():
            if (x := 1) == 1:
                print(x)

    def test_if_walrus_2(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                if (x := 1) == 1:
                    print(x)
                print(x)

    def test_if_walrus_3(self):
        @block_scoping
        def f():
            if (x := 1) == 1 and (y := 3) == 3:
                print(x)
                print(y)

    def test_while_walrus_1(self):
        @block_scoping
        def f():
            num = 1
            while (square := num ** 2) <= 10:
                print(square)
                num += 1

    def test_while_walrus_2(self):
        @block_scoping
        def f():
            num = 1
            while (square := num ** 2) <= 10 and (y := 1) == 1:
                print(square)
                print(y)
                num += 1

    def test_comprehension_walrus1(self):
        @block_scoping
        def f():
            nums = [1, 2, 3, 4, 5]
            total_sum = 0
            cumulative_sums = [(total_sum := total_sum + num) for num in nums]
   
    def test_ternary_walrus1(self):
        @block_scoping
        def f():
            label = "High" if (threshold := 80) < 100 else "Low"
            print(threshold)

    def test_basic_walrus1(self):
        @block_scoping
        def f():
            c = (result := 4)
            print(result)

    def test_dataclass(self):
        @block_scoping
        @dataclass
        class A:
            v1: int
            def method(self):
                print(self.v1)


if __name__ == '__main__':
    unittest.main(verbosity=2)