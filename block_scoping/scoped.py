import inspect
import builtins
import ast
import re
import textwrap
from contextlib import contextmanager

@contextmanager
def block_scope():
    yield


class WalrusVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.assign_targets = []

    def visit_NamedExpr(self, node):
        if isinstance(node.target, ast.Name):
            self.assign_targets.append(node.target.id)

class BlockScopingException(Exception):
    pass


def _extract_assign_vars(target_node) -> list:
    assert isinstance(target_node, ast.AST)

    result = []
    def extract_rec(target):
        if isinstance(target, ast.Name):
            result.append(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                extract_rec(element)
        elif isinstance(target, ast.Starred):
            extract_rec(target.value)
        elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) \
            and target.value.id == "self" and isinstance(target.value.ctx, ast.Load):
            result.append(f"self.{target.attr}")

    extract_rec(target_node)

    return result

def _extract_comprehension_vars(node) -> list:
    result = []
    for generator in node.generators:
        if isinstance(generator.target, ast.Name):
            result.append(generator.target.id)
        elif isinstance(generator.target, ast.Tuple):
            for elt in generator.target.elts:
                if isinstance(elt, ast.Name):
                    result.append(elt.id)

    return result

def _decorated_to_skip_checking(node) -> bool:
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == no_block_scoping.__name__:
            return True

    return False


builtin_var = re.compile("__(.+)__")


class ImportVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
            if alias.asname:
                self.imports.append(alias.asname)
            else:
                self.imports.append(alias.name.split('.')[0])

    def visit_ImportFrom(self, node):
        for alias in node.names:
            if alias.name != '*':
                self.imports.append(f"{node.module}.{alias.name}")
            self.imports.append(alias.asname or alias.name)

class ScopeChecker(ast.NodeVisitor):
    def __init__(
            self,
            global_vars: list[str],
            obj_attrs: list[str],
            attr_check: bool,
            func_name: str=None,
            filename: str=None) -> None:
        self._scopes = [set(global_vars).union(dir(builtins)).union(obj_attrs)]
        self._for_loop_vars = set([])
        self._func_name = func_name
        self._filename = filename
        self._attr_check = attr_check

        self.last_func_scope = set([])  # contains the scope of the last function called
        self.errors = []

    def _loc(self, node) -> str:
        if self._filename:
            return f"around line {node.lineno} of {self._filename}"
        else:
            return f"around line {node.lineno} of {self._func_name}"

    def _error(self, node, msg: str):
        msg = f"Block scoping issue {self._loc(node)}: {msg}"
        self.errors.append(msg)
        if self._filename is None:
            raise BlockScopingException(msg)

    @contextmanager
    def _scope(self, extra_vars=[]):
        self._scopes.append(set(extra_vars))
        yield
        self._scopes.pop()

    def _check_in_scope(self, node, v: str):
        if builtin_var.match(v):
            return  # variables like __name__ and __file__

        for scope in self._scopes:
            if v in scope:
                return

        in_scope = set()  # only for the error message
        for x in self._scopes[1:]:
            in_scope.update(x)

        self._error(
            node,
            f"Variable '{v}' cannot be found in scope. Variables in scope: {in_scope}"
        )
        
    def _walrus_targets(self, node) -> list[str]:
        """ you can only call this on a if-like structure """

        tmp_visitor = WalrusVisitor()
        tmp_visitor.visit(node.test)
             
        return tmp_visitor.assign_targets

    def visit_Attribute(self, node):
        """ check only attributes of 'self' """
        if self._attr_check:
            self._check_in_scope(node, f"self.{node.attr}")

        self.generic_visit(node)

    def visit_Assign(self, node):
        """ Adds variables to current scope and checks that assignments do not overwite for-loop variables """
        current_scope = self._scopes[-1]
        for target in node.targets:
            for new_var in _extract_assign_vars(target):
                current_scope.add(new_var)
                # not enforcing this for now:
                # if new_var in self._for_loop_vars:
                #     self._error(
                #         node,
                #         f"Cannot reassign {new_var} as it is used for iterating in a parent for-loop"
                #     )

        self.generic_visit(node)

    def visit_AugAssign(self, node):
        for v in _extract_assign_vars(node.target):
            # not enforcing this for now:
            # if v in self._for_loop_vars:
            #     self._error(
            #         node.target,
            #         f"Cannot reassign '{v}' as it is used for iterating over a parent for-loop"
            #     )
            self._check_in_scope(node, v)

        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self._check_in_scope(node, node.id)

    def visit_FunctionDef(self, node):
        if _decorated_to_skip_checking(node):
            return
    
        # add function to current scope
        self._scopes[-1].add(node.name)

        with self._scope([arg.arg for arg in node.args.args]):
            self.generic_visit(node)
            self.last_func_scope = set(self._scopes[-1])  # most notably, this will contain the object attributes for __init__

    def visit_DictComp(self, node):
        new_vars = _extract_comprehension_vars(node)
        with self._scope(new_vars):
            self.visit(node.key)
            self.visit(node.value)
            for g in node.generators:
                for cond in g.ifs:
                    self.visit(cond)

    def visit_ListComp(self, node):
        new_vars = _extract_comprehension_vars(node)
        with self._scope(new_vars):
            self.visit(node.elt)
            for g in node.generators:
                for cond in g.ifs:
                    self.visit(cond)

    def visit_SetComp(self, node):
        self.visit_ListComp(node)

    def visit_ClassDef(self, node):
        if _decorated_to_skip_checking(node):
            return

        self.generic_visit(node)

    def visit_Lambda(self, node):
        with self._scope([arg.arg for arg in node.args.args]):
            self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_For(self, node):
        target = node.target
        
        ite = []
        # the 'ite' in 'for ite1, ite2 in range(10)' 
        if isinstance(target, ast.Name):
            ite = [target.id]
        elif isinstance(target, ast.Tuple):
            ite = [elt.id for elt in target.elts if isinstance(elt, ast.Name)]

        # check that we are not reusing a parent's for loop variables
        for v in ite:
            if v in self._for_loop_vars:
                self._error(
                    target,
                    f"Cannot reuse variable '{v}' as it is already used by another for-loop"
                )

        self._for_loop_vars.update(ite)

        with self._scope(extra_vars=ite):
            self.generic_visit(node)

        for v in ite:
            if v in self._for_loop_vars:
                # since self._error is blocking in script mode,
                # the same variable can be removed twice
                self._for_loop_vars.remove(v)

    def visit_AsyncFor(self, node):
        self.visit_For(node)

    def visit_While(self, node):
        extra = self._walrus_targets(node)
        with self._scope(extra):
            self.generic_visit(node)

    def visit_If(self, node):
        # the main IF
        walrus_vars = self._walrus_targets(node)
        with self._scope(extra_vars=walrus_vars):
            for stmt in node.body:
                self.visit(stmt)

        current_node = node
        while current_node.orelse:
            if isinstance(current_node.orelse[0], ast.If):
                # the elifs (if any)
                ifelse_node = current_node.orelse[0]
                walrus_vars += self._walrus_targets(ifelse_node)
                with self._scope(extra_vars=walrus_vars):
                    for stmt in ifelse_node.body:
                        self.visit(stmt)
                current_node = ifelse_node
            else:
                # Else block
                with self._scope(extra_vars=walrus_vars):
                    for stmt in current_node.orelse:
                        self.visit(stmt)
                break

    def visit_Try(self, node):
        # 'except' blocks can't use the variables defined in the try and else,
        # and they can't add variables to the main scope
        for handler in node.handlers:
            with self._scope():
                self.visit(handler)

        # the 'try' block
        for stmt in node.body:
            self.visit(stmt)

        # the 'else' block
        if node.orelse:
            for stmt in node.orelse:
                self.visit(stmt)

        # the 'finally' block
        if node.finalbody:
            for stmt in node.finalbody:
                self.visit(stmt)

    def visit_With(self, node):
        new_vars = []
        for item in node.items:  # there could be multiple withs
            if item.optional_vars:
                # TODO: find a way to make this available only inside the with
                vars = _extract_assign_vars(item.optional_vars)
                new_vars += vars

        context_expr = node.items[0].context_expr
        if isinstance(context_expr, ast.Call) and isinstance(context_expr.func, ast.Name) \
            and context_expr.func.id == "block_scope":
            # only create a scope for statements like: 'with block_scope():'
            with self._scope(extra_vars=new_vars):
                self.generic_visit(node)
        else:
            self._scopes[-1].update(new_vars)
            self.generic_visit(node)

    def visit_AsyncWith(self, node):
        self.visit_With(node)

    def visit_NamedExpr(self, node):
        # walrus operator
        if isinstance(node.target, ast.Name):
            self._scopes[-1].add(node.target.id)
        self.generic_visit(node)

    def visit_Match(self, node):
        pass
        # TODO: extract new variables in patterns

    def visit_Import(self, node):
        visitor = ImportVisitor()
        visitor.visit(node)
        self._scopes[-1].update(visitor.imports)

    def visit_ImportFrom(self, node):
        visitor = ImportVisitor()
        visitor.visit(node)
        self._scopes[-1].update(visitor.imports)


def _check_func(func_ast, scope_vars: list, attr_check: bool, obj_attrs=[], filename:str=None) -> tuple:
    checker = ScopeChecker(
        scope_vars,
        obj_attrs=obj_attrs,
        attr_check=attr_check,
        func_name=func_ast.name,
        filename=filename
    )
    checker.visit(func_ast)

    return checker.last_func_scope, checker.errors

def _check_class(class_ast, scope_vars: list, filename:str=None) -> list:
    is_sub_class = True if class_ast.bases else False

    # fetch variables/function at the top-level of the class
    class_level_vars = []
    method_nodes = {}
    for item in class_ast.body:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    class_level_vars.append(target.id)
        elif isinstance(item, ast.FunctionDef):
            method_nodes[item.name] = item

    scope_vars += class_level_vars
    scope_vars += [f"self.{m}" for m in method_nodes.keys()]

    all_errors = []

    # check the __init__ and get the variables initialized in the init
    init_method = method_nodes.get('__init__')
    obj_attrs = [f"self.{v}" for v in class_level_vars]  # class vars can be accessed with self
    if init_method is not None:
        vars_in_scope, errors = _check_func(init_method, scope_vars, attr_check=False, filename=filename)
        obj_attrs = [attr for attr in vars_in_scope if attr.startswith("self.")]
        all_errors += errors

    # check the other methods
    for method_name, method_ast in method_nodes.items():
        if method_name != '__init__':
            # we've already checked __init__, that's why we skip it
            _, errors = _check_func(
                method_ast,
                scope_vars,
                obj_attrs=obj_attrs,
                attr_check=not is_sub_class,
                filename=filename
            )
            all_errors += errors

    return all_errors

def block_scoping(class_or_func):
    global_vars = list(
        inspect.getmodule(class_or_func).__dict__.keys()  # this includes imports
    )
    source = inspect.getsource(class_or_func)
    source = textwrap.dedent(source)
    tree = ast.parse(source)

    node = None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            break

    assert node is not None, f"no function or class found in {source}"

    if isinstance(class_or_func, type):  # if it's a class
        _check_class(node, scope_vars=global_vars)
    elif callable(class_or_func):  # if it's a function
        _check_func(node, scope_vars=global_vars, attr_check=False)
    else:
        raise TypeError("block_scoping decorator must be applied to a function or a class.")

    return class_or_func

def no_block_scoping(class_or_func):
    return class_or_func

