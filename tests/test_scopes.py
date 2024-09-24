import unittest
import ast
from block_scoping import block_scoping, no_block_scoping, block_scope, BlockScopingException
from block_scoping.scoped import _extract_assign_vars
from contextlib import suppress

def parse_single_line(line: str):
    return ast.parse(line).body[0]

def assign_vars(tree):
    if hasattr(tree, 'target'):
        yield from _extract_assign_vars(tree.target)
    else:
        for t in tree.targets:
            yield from _extract_assign_vars(t)

class TestBlockScoping(unittest.TestCase):

    def test_extract_assign_vars1(self):
        tree = parse_single_line("a = 4")
        assert list(assign_vars(tree)) == ['a']

    def test_extract_assign_vars2(self):
        tree = parse_single_line("a, b = 4, 4")
        assert list(assign_vars(tree)) == ['a', 'b']

    def test_extract_assign_vars3(self):
        tree = parse_single_line("[a, b] = 4, 4")
        assert list(assign_vars(tree)) == ['a', 'b']

    def test_extract_assign_vars4(self):
        tree = parse_single_line("a, (b, c) = 4, (4, 5)")
        assert list(assign_vars(tree)) == ['a', 'b', 'c']

    def test_extract_assign_vars5(self):
        tree = parse_single_line("((a,b), ((c, d), e)) = ((1,2), ((3, 4), 5))")
        assert list(assign_vars(tree)) == ['a', 'b', 'c', 'd', 'e']

    def test_extract_assign_vars6(self):
        tree = parse_single_line("self.a = 1")
        assert list(assign_vars(tree)) == ['self.a']

    def test_extract_assign_vars7(self):
        tree = parse_single_line("self.a.c = 1")
        assert list(assign_vars(tree)) == []

    def test_extract_assign_vars8(self):
        tree = parse_single_line("self.a, self.b = 1, 2")
        assert list(assign_vars(tree)) == ['self.a', 'self.b']

    def test_extract_assign_vars8(self):
        tree = parse_single_line("self.a, (self.b, self.c) = 1, (2, 3)")
        assert list(assign_vars(tree)) == ['self.a', 'self.b', 'self.c']

    def test_extract_assign_vars9(self):
        tree = parse_single_line("a, *b, c = 4, 4, 5, 5, 5")
        assert list(assign_vars(tree)) == ['a', 'b', 'c']

    def test_extract_assign_vars10(self):
        tree = parse_single_line("x += 3")
        assert list(assign_vars(tree)) == ['x']
    
    def test_scoped_loop1(self):
        @block_scoping
        def f():
            outside = 1
            for x in [1, 2, 3]:
                outside = 2

            print(outside)

    def test_scoped_loop2(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                for x in [1, 2, 3]:
                    outside = 2

                print(outside)

    def test_basic(self):
        @block_scoping
        def f():
            x = 1
            print(x)

    def test_nested(self):
        @block_scoping
        def f():
            def inner():
                return 1
            inner()

    def test_with(self):
        @block_scoping
        def f():
            with suppress(ValueError):
                y = 2
            print(y)

    def test_with_block_scope(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                with block_scope():
                    y = 2
                print(y)

    def test_elif(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                if False:
                    x = 1
                elif True:
                    y = 2
                else:
                    z = 3
                print(y)

    def test_for_loop_iterator1(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                for i in range(5):
                    pass
                print(i)

    # not enforced for now:

    # def test_for_loop_iterator2(self):
    #     with self.assertRaises(BlockScopingException):
    #         @block_scoping
    #         def f():
    #             for i in range(5):
    #                 i = 2

    # def test_for_loop_iterator3(self):
    #     with self.assertRaises(BlockScopingException):
    #         @block_scoping
    #         def f():
    #             for i in range(5):
    #                 i += 2

    def test_for_loop_iterator4(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                for i in range(5):
                    for i in range(6):
                        print(i)

    
    def test_for_loop_iterator5(self):
        @block_scoping
        def f():
            for i in range(5):
                print(i)
                for j in range(6):
                    print(i, j)

    def test_unknown_function(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                unknown_func()

    def test_recursive_function(self):
        @block_scoping
        def f_rec(h):
            print(h)
            if h == 0:
                f_rec(h-1)

    def test_while_loop(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                while True:
                    x = 1
                print(x)

    def test_complex_assignment(self):
        @block_scoping
        def f():
            a, b, (c, d) = 1, 2, (3, 4)
            print(a)
            print(b)
            print(c)
            print(d)

    def test_try_expect1(self):
        @block_scoping
        def f():
            try:
                x = 1
            except:
                y = 1
            else:
                z = 1
            print(x)
            print(z)

    def test_try_expect1(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                try:
                    x = 1
                except:
                    y = 1
                else:
                    z = 1
                print(y)

    def test_lambda_function(self):
        @block_scoping
        def f():
            x = 1
            l = lambda y: x + y


    def test_non_local(self):
        @block_scoping
        def f():
            x = 1
            def inner():
                nonlocal x
                x = 2
            print(x)

    def test_with1(self):
        @block_scoping
        def f():
            with suppress(BlockScopingException):
                x = 1
            print(x)

    def test_with2(self):
        @block_scoping
        def f(a):
            with a.block():
                x = 1

    def test_scoped_with(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                with block_scope():
                    x = 1
                print(x)

    def test_inner_function(self):
        @block_scoping
        def f(a):
            def inner():
                print(a)
            inner()

    def test_list_comprehension1(self):
        @block_scoping
        def f(a):
            return [a*x for x in (1, 2, 3)]

    def test_list_comprehension2(self):
        @block_scoping
        def f(a):
            return [a*x*y*z for x in (1, 2, 3) for (y, z) in ((1, 1) , (2, 2))]

    def test_list_comprehension3(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                return [a*x for x in (1, 2, 3)]

    def test_set_comprehension1(self):
        @block_scoping
        def f(a):
            return {a*x for x in (1, 2, 3)}

    def test_set_comprehension2(self):
        @block_scoping
        def f(a):
            return {a*x*y*z for x in (1, 2, 3) for (y, z) in ((1, 1) , (2, 2))}

    def test_set_comprehension3(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                return {a*x for x in (1, 2, 3)}

    def test_dict_comprehension1(self):
        @block_scoping
        def f(a):
            return {a*x: x for x in (1, 2, 3)}

    def test_dict_comprehension2(self):
        @block_scoping
        def f(a):
            return {a*x*y*z: x+y+z for x in (1, 2, 3) for (y, z) in ((1, 1) , (2, 2))}

    def test_dict_comprehension3(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                return {x: a for x in (1, 2, 3)}

    def test_dict_comprehension3(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                return {a: x for x in (1, 2, 3)}

    def test_list_assignment1(self):
        @block_scoping
        def f():
            x = [1, 2, 3]
            x[:] = [3, 4, 5]

    def test_list_assignment2(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                y[:] = [3, 4, 5]

    def test_element_assignment1(self):
        @block_scoping
        def f():
            x = [1, 2, 3]
            x[1] += 3

    def test_element_assignment2(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                x[1] += 3

    def test_element_assignment3(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                x[1] = 3

    def test_element_assignment4(self):
        @block_scoping
        def f():
            x = [0]
            x[1] = 3

    def test_element_assignment5(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                x[:] = [1, 2]

    def test_aug_assign1(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                x += 3

    def test_aug_assign2(self):
        @block_scoping
        def f():
            x = 1
            x += 3

    def test_class_method_attribute_access(self):
        @block_scoping
        class MyClass:
            def __init__(self):
                self.a = 10

            def method(self):
                print(self.a)

    def test_class_method_attribute_access_error(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            class MyClass:
                def method(self):
                    print(self.a)

    def test_no_block_scoping_decorator(self):
        @no_block_scoping
        def f():
            outside = 1

    def test_access_before_assignment(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                print(x)
                x = 10

    def test_function_arguments_usage(self):
        @block_scoping
        def f(a, b):
            print(a + b)

    def test_class_with_static_method(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            class MyClass:
                @staticmethod
                def static_method():
                    print(self.a)

    def test_access_self_attribute_outside_init(self):
        @block_scoping
        class MyClass:
            def __init__(self):
                self.a = 10

            def method(self):
                print(self.a)

    def test_access_self_attribute_outside_init2(self):
        @block_scoping
        class MyClass:
            def method(self):
                self.a = 4
                print(self.a)

    def test_access_self_attribute_not_initialized(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            class MyClass:
                def method(self):
                    print(self.a)

    def test_import_assignment(self):
        @block_scoping
        def f():
            import math
            print(math.pi)

    def test_variable_defined_in_else_block(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                if False:
                    pass
                else:
                    x = 10
                print(x)

    def test_class_inheritance(self):
        @block_scoping
        class Base:
            def __init__(self):
                self.base_attr = 1

        @block_scoping
        class Derived(Base):
            def __init__(self):
                super().__init__()
                self.derived_attr = 2

            def method(self):
                print(self.base_attr)
                print(self.derived_attr)

    def test_class_inheritance(self):
        class Base:
            def __init__(self):
                pass  # base_attr not initialized

        @block_scoping
        class Derived(Base):
            def method(self):
                print(self.base_attr)  # base_attr not initialized

    def test_static_method_without_self(self):
        @block_scoping
        class MyClass:
            @staticmethod
            def static_method(x):
                return x * 2

    def test_variable_defined_in_nested_function_used_outside(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                def inner():
                    x = 10
                inner()
                print(x)

    def test_variable_defined_in_finally_used_outside(self):
        @block_scoping
        def f():
            try:
                pass
            finally:
                y = 2
            print(y)

    def test_variable_defined_in_comprehension_used_outside(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                [x for x in range(5)]
                print(x)

    def test_class_variable_access_in_instance_method(self):
        @block_scoping
        class MyClass:
            class_var = 10
            def method(self):
                print(self.class_var)  # Should be acceptable


    def test_multiple_assignments_in_single_line(self):
        @block_scoping
        def f():
            a = b = c = 10
            print(a, b, c)
        try:
            f()
        except BlockScopingException:
            self.fail("BlockScopingException was raised unexpectedly for multiple assignments in single line.")

    def test_with_variable1(self):
        @block_scoping
        def f():
            with suppress(ValueError) as v:
                print(v)

    # this is not supported yet
    # def test_with_variable2(self):
    #     with self.assertRaises(BlockScopingException):
    #         @block_scoping
    #         def f():
    #             with suppress(ValueError) as v:
    #                 print(v)
    #             print(v)

    def test_multiple_withs(self):
        @block_scoping
        def f():
            with suppress(ValueError) as v1, suppress(ValueError) as v2:
                print(v1, v2)

    def test_regular_self_access(self):
        @block_scoping
        class A:
            def method(self):
                self.a = "x"
                print(self.a)

    def test_complex_for(self):
        @block_scoping
        def f():
            for (x, y), z in [((1, 2), 3)]:
                print(x, y)
    
    def test_error_variable(self):
        @block_scoping
        def f():
            try:
                pass
            except (ValueError, ZeroDivisionError) as e:
                print(f"An error occurred: {e}")

    def test_starred_variables1(self):
        @block_scoping
        def f(*args, **kwargs):
            print(args, kwargs)

    def test_starred_variables2(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                y = {**x}

    def test_object_method1(self):
        @block_scoping
        class A:
            def __init__(self):
                self.a = "x"
                self.a.method()

    def test_object_method2(self):
        @block_scoping
        class A:
            def __init__(self):
                self.method()

    def test_object_method3(self):
        @block_scoping
        def f():
            return "xxxxx".lower()

    def test_object_method4(self):
        @block_scoping
        def f():
            v = "xxxxx"
            return v.lower()

    def test_object_method5(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                return v.lower()


    def test_if_else_scope_inheritance1(self):
        @block_scoping
        def f():
            if True:
                x = 1
            else:
                x = 2
            print(x)

    def test_if_else_scope_inheritance2(self):
        @block_scoping
        def f():
            if True:
                x = 1
            elif False:
                x = 3
            else:
                x = 2
            print(x)

    def test_if_else_scope_inheritance3(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                if True:
                    x = 1
                elif False:
                    x = 3
                print(x)

    def test_if_else_scope_inheritance_nested1(self):
        @block_scoping
        def f():
            if True:
                if True:
                    x = 1
                else:
                    x = 2
            else:
                if True:
                    x = 2
                else:
                    x = 3
            print(x)

    def test_if_else_scope_inheritance_nested2(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                if True:
                    if True:
                        x = 1
                else:
                    if True:
                        x = 2
                    else:
                        x = 3
                print(x)

    def test_if_else_scope_inheritance_nested3(self):
        with self.assertRaises(BlockScopingException):
            @block_scoping
            def f():
                if True:
                    if True:
                        x = 1
                    else:
                        x = 2
                else:
                    if True:
                        x = 2
                print(x)

    def test_allow_underscore_reuse(self):
        @block_scoping
        def f():
            for _ in range(3):
                for _ in range(5):
                    pass

    def test_class_var1(self):
        @block_scoping
        class A:
            v1 = 3
            def __init__(self):
                print(self.v1)

    def test_class_var2(self):
        @block_scoping
        class A:
            v1 = 3
            def method(self):
                print(self.v1)

    def test_class_var3(self):
        @block_scoping
        class A:
            v1 = 3

            def __init__(self):
                pass

            def method(self):
                print(self.v1)


    def test_init_subclass(self):
        @block_scoping
        class A:
            def __init__(self):
                if True:
                    self._init_vars()
                else:
                    self._init_vars()

            def _init_vars(self):
                if True:
                    self._deep()
                else:
                    self._deep()

            def _deep(self):
                self.x = 3

            def method(self):
                print(self.x)


if __name__ == '__main__':
    unittest.main(verbosity=2)