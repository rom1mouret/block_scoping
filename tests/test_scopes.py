import unittest
from block_scoping import scoped, condition, loop, when, block_scopable

class TestBlockScoping(unittest.TestCase):
    def test_scoped_loop(self):
        outside1 = 1
        outside2 = 1
        for x in loop([1, 2, 3], keep=('k', 'z')):
            outside1 = 2
            y = 1
            k = 1
            z = 1

        assert outside1 == 2
        assert outside2 == 1
        assert k == 1
        assert z == 1

        try:
            assert y == 1
        except UnboundLocalError:
            pass
        else:
            raise Exception("proper exception should have been raised")

        try:
            assert x > 0
        except UnboundLocalError:
            pass
        else:
            raise Exception("proper exception should have been raised")

    @block_scopable
    def test_scoped_if_true1(self):
        outside1 = 1
        outside2 = 1
        with condition(True, keep=('k', 'z')):
            outside1 = 2
            y = 1
            k = 1
            z = 1

        assert outside1 == 2
        assert outside2 == 1
        assert k == 1
        assert z == 1

        try:
            assert y == 1
        except UnboundLocalError:
            pass
        else:
            raise Exception("proper exception should have been raised")

    @block_scopable
    def test_scoped_condition_true2(self):
        outside1 = 1
        outside2 = 1
        with condition(True) as s:
            outside1 = 2
            y = 1
            k = 1
            z = 1
            s.keep('k', 'z')

        assert outside1 == 2
        assert outside2 == 1
        assert k == 1
        assert z == 1

        try:
            assert y == 1
        except UnboundLocalError:
            pass
        else:
            raise Exception("proper exception should have been raised")

    @block_scopable
    def test_scoped_condition_false(self):
        outside = 1
        with condition(False) as s:
            k = 1
            outside = 2
            s.keep('k')

        assert outside == 1

        try:
            assert k == 1
        except UnboundLocalError:
            pass
        else:
            raise Exception("proper exception should have been raised")

    def test_missing_block_scopable(self):
        try:
            with condition(False):
                pass
        except:
            pass
        else:
            raise Exception("proper exception should have been raised")

    def test_when_true(self):
        outside1 = 1
        outside2 = 1
        if s := when(True):
            outside1 = 2
            y = 1
            k = 1
            z = 1
            s.keep('k', 'z')
            s.destroy()

        assert outside1 == 2
        assert outside2 == 1
        assert k == 1
        assert z == 1

        try:
            assert y == 1
        except UnboundLocalError:
            pass
        else:
            raise Exception("proper exception should have been raised")

    def test_when_false(self):
        outside = 1
        if s := when(False):
            k = 1
            outside = 2
            s.keep('k')
            s.destroy()

        assert outside == 1

        try:
            assert k == 1
        except UnboundLocalError:
            pass
        else:
            raise Exception("proper exception should have been raised")


    def test_scoped(self):
        outside1 = 1
        outside2 = 1
        with scoped(keep=('k', 'z')):
            outside1 = 2
            y = 1
            k = 1
            z = 1

        assert outside1 == 2
        assert outside2 == 1
        assert k == 1
        assert z == 1

        try:
            assert y == 1
        except UnboundLocalError:
            pass
        else:
            raise Exception("proper exception should have been raised")


if __name__ == '__main__':
    unittest.main(verbosity=2)