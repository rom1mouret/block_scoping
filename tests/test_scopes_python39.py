import unittest
from dataclasses import dataclass
from block_scoping import block_scoping, BlockScopingException

class TestBlockScoping(unittest.TestCase):

    def test_match1(self):
        @block_scoping
        def f():
            x = 3
            match x:
                case 2:
                    print(x)
                case 3:
                    pass

    def test_match2(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                x = 3
                match x:
                    case 2:
                        y = 3
                    case 3:
                        pass

                print(y)

if __name__ == '__main__':
    unittest.main(verbosity=2)