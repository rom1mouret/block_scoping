import inspect
import ctypes
import sys
import ast
import textwrap
from types import FunctionType
from contextlib import contextmanager

def _normalize_var_list(keep):
    if isinstance(keep, str):
        keep = (keep, )
    elif isinstance(keep, tuple) or isinstance(keep, list):
        if len(keep) > 3:
            keep = set(keep)  # faster membership testing
    elif isinstance(keep, set):
        pass
    else:
        raise TypeError("argument 'keep' must be string, a tuple, a list or a set")

    # TODO: test type of inside variables

    return keep


class Scope:
    def __init__(self, up: int) -> None:
        self._destroyed = False
        self._keep = None
        self._up = up
        frame_info = inspect.stack()[self._up]
        # for potential error logging:
        self._error_loc = f"line {frame_info.lineno} of {frame_info.filename} (function '{frame_info.function}')"

        self._frame = frame_info[0]
        self._before_scope_vars = set(self._frame.f_locals.keys())

    def keep(self, *vars_to_keep) -> None:
        self._keep = list(vars_to_keep)

    def destroy(self, keep=[]) -> None:
        if self._destroyed:
            return

        if self._keep:
            if keep:
                print(f"WARNING: variables to keep are set twice somewhere around {self._error_loc}", file=sys.stderr)
            keep = _normalize_var_list(self._keep)
        else:
            keep = _normalize_var_list(keep)

        after_scope_vars_dict = self._frame.f_locals
        after_scope_vars = set(after_scope_vars_dict.keys())

        for var_to_keep in keep:
            if var_to_keep not in after_scope_vars:
                print(f"WARNING: variable '{var_to_keep}' not found in scope defined somewhere around {self._error_loc}", file=sys.stderr)       

        for key in after_scope_vars:
            if key not in self._before_scope_vars and key not in keep:
                after_scope_vars_dict.pop(key)

        # make sure the removal of the variable is synced:
        ctypes.pythonapi.PyFrame_LocalsToFast(
            ctypes.py_object(self._frame),
            ctypes.c_int(1)
        )
        self._destroyed = True

    def __del__(self) -> None:
        if not self._destroyed:
            print(f"WARNING: scope not destroyed somewhere around {self._error_loc}", file=sys.stderr)


def loop(seq, keep=[]):
    """ """
    scope = Scope(up=2)  # up=2 accounts for the __init__
    try:
        for x in seq:
            yield x
    finally:
        scope.destroy(keep=keep)


def when(b: bool, keep=[]) -> Scope:
    """ """
    if not b:
        return None
    
    return Scope(up=2)  # up=2 accounts for the__init__


@contextmanager
def condition(b: bool, keep=[]):
    """ """
    # TODO: check that b is bool (it has to be constant)
    if not b:
        raise Exception("You cannot use 'condition' without annotating your function with @block_scope_friendly")

    scope = Scope(up=3)  # up=3 accounts for the __enter__ + __init__
    try:
        yield scope
    finally:
        scope.destroy(keep=keep)

@contextmanager
def scoped(keep=[]):
    """ """
    scope = Scope(up=3)  # up=3 accounts for the __enter__ + __init__
    try:
        yield scope
    finally:
        scope.destroy(keep=keep)



class ScopedIfTransformer(ast.NodeTransformer):
    def visit_With(self, node):
        """ Insert an IF before scope_if to prevent its block from being executed if condition is not met """
        first = node.items[0].context_expr
        if isinstance(first, ast.Call) and isinstance(first.func, ast.Name) and first.func.id == 'condition':
            condition = node.items[0].context_expr.args[0]
            return ast.If(
                test=condition,
                body=[node],
                orelse=[]
            )
        return node

    def visit_If(self, node):
        """ Insert a call to scope.destroy() at the end of the if """
        t = node.test
        if isinstance(t, ast.Call) and isinstance(t.func, ast.Name) and t.func.id in ('when', 'nomatch'):
            result_var = 'when_scope'
            # Create a new variable to store the result of when()
            var_name = ast.Name(id=result_var, ctx=ast.Store())
            assign = ast.Assign(targets=[var_name], value=node.test)

            # Create the method call on the new variable
            destroy_call = ast.Expr(
                ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id=result_var, ctx=ast.Load()),
                        attr='destroy',
                        ctx=ast.Load()
                    ),
                    args=[],
                    keywords=[]
                )
            )

            # # Recursively transform the body and orelse
            # new_body = [self.visit(stmt) for stmt in node.body]
            # new_orelse = [self.visit(stmt) for stmt in node.orelse]
                
            # Modify the if statement
            new_if = ast.If(
                test=ast.Name(id=result_var, ctx=ast.Load()),
                body=node.body + [destroy_call],
                orelse=node.orelse
            )

            #TODO: raise error if there is an else:
            # TODO: nomatch(keep='all')  

            # Return a new AST with the assignment followed by the modified if
            return [assign, new_if]

        return node

def block_scopable(func):
    """ Insert an IF before scope_if to prevent its block from being executed if condition is not met  """
    source = inspect.getsource(func)
    source = textwrap.dedent(source)  # normalize the indentation, otherwise it doesn't compile
    tree = ast.parse(source)
    new_tree = ScopedIfTransformer().visit(tree)
    ast.fix_missing_locations(new_tree)
    code = compile(new_tree, "<string>", "exec")

    return FunctionType(
        code.co_consts[0],
        func.__globals__,
        func.__name__,
        func.__defaults__,
        func.__closure__
    )


if __name__ == "__main__":
    @block_scopable
    def foobar():
        x = 1
        if when(True):
            x = 1
            y = 2
        print("x", x)
        print("y", y)

    foobar()

    # TODO: test nested condition
    # TODO: test when is not called twice

