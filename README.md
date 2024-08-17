# Block Scoping

Python's lack of block scoping is a common source of bugs.

[This package](https://github.com/l74d/scoping) addresses this problem.
However, it may not be the best fit for your codebase due to:

1. The additional indentation required for `for` loops and `if` statements;
2. The implementation of [shadowing](https://en.wikipedia.org/wiki/Variable_shadowing), which is not a feature I want enabled by default.

Because Python doesn't have a `var`/`let` keyword, shadowing makes this code unintuitive and difficult to understand, unless you explicitely tell `scoping` to keep `x` after the end of the scope.

```python3
from scoping import scoping  # shawoding implementation from https://github.com/l74d/scoping
x = None
with scoping():
    if x is None:
        x = 3
print(x)  # 'None' is printed
```

In contrast, my package aims at keeping things intuitive and convenient.
Below are some examples.

## Scoped Loop

```python3

from block_scoping import loop

outside = 0
for x in loop([1, 2, 3], keep='z'):
    outside += 1
    y = 1
    z = 1

print(x)  # raises error
print(y)  # raises error
print(outside)  # prints '3', i.e. no variable shadowing
print(z)  # prints '1'
```

## Standalone IFs

Standalone IFs are best handled with a `condition` construct:

```
@block_scopable
def foobar():
    outside = None
    with condition(outside is None):
        outside = 1
        y = 1
    print(y)  # raises error
    print(outside)  # prints '1', i.e. no variable shadowing
```

Unlike other constructs, you will need to annotate the parent function/method with `@block_scopable`.
It will raise an error if the annotation is missing and the condition is false.

You can specify which variables to keep, as for `loop`:

```
@block_scopable
def foobar():
    outside = None
    with condition(outside is None, keep='z'):
        outside = 1
        y = 1
        z = 1
    print(z)  # prints '1'
```

Alternatively, you can specify the variables to keep with the `keep` method:

```
@block_scopable
def foobar():
    with condition(True) as c:
        y = 1
        z = 1
        c.keep('y', 'z')  # anywhere in the block
    print(y)  # prints '1'
    print(z)  # prints '1'
```


## If/Elif/Else

For if/elif/else scenarios, it is recommended to wrap everything into a plain `scoped`:

```python3

from block_scoping import scoped

outside = None
a = 3
with scoped(keep='z'):
    y = 4
    if a == 1:
        outside = 1
        z = 1
    elif a == 2:
        outside = 2
        z = 2
    else:
        outside = 3
        z = 3
print(y)  # raises error
print(outside)  # prints '3'
print(z)  # prints '3'
```

Or, equivalently:
```python3

from block_scoping import scoped

outside = None
a = 3
with scoped() a s:
    y = 4
    if a == 1:
        outside = 1
        z = 1
    elif a == 2:
        outside = 2
        z = 2
    else:
        outside = 3
        z = 3
    s.keep('z')
print(y)  # raises error
print(outside)  # prints '3'
print(z)  # prints '3'
```

If you really don't like the extra indent, you can also use `when` with the walrus operator:


```python3

outside = None
a = 3
if s := when(a == 1):
    outside = 1
    z = 1
    s.destroy(keep='z')
elif s := when(a == 2):
    outside = 2
    z = 2
    s.destroy(keep='z')
elif s := when(True):
    outside = 3
    z = 3
    s.destroy(keep='z')

print(y)  # raises error
print(outside)  # prints '3'
print(z)  # prints '3'
```

Note that you will have to explicitely destroy the scope with the `destroy` method.
You will be reminded if you haven't called `destroy` by the time the `scope` is garbage collected.

# External Contribution

Contributions are welcomed!


```
if when(a == 1):
    pass

elif when(a == 2):
    pass

elif when(True):
    pass

```

when(a == 1, keep='x'):
    pass
    
if s := when(a == 1):
    s.keep('x')