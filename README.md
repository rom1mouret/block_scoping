# Block Scoping

This is simple [PyPi package](https://pypi.org/project/block-scoping/) running static analysis to detect scoping issues caused by Python's lack of block scoping.

Python's scoping is a common source of bugs.

### Example

```python3
total = 0
for item in items:
    if item > 0:
        total += item
    else:
        skipped = True
    
if skipped:
    print("Some items have been skipped")
```

The mistake is easy to spot. However, in larger codebases, such issues can be much harder to detect.


### Another Example

```python3
try:
    x = int(y)
    f(x)
except:
    logging.error(f"error when x = {x}")
```

The intent is to catch errors raised by `f`, but this could also catch errors raised by `int(y)`, which this `except` is not prepared for.

To avoid these potential bugs, it's safer not to reference any variable in the `except` block that was defined within the `try` block. A simple fix would be:

```python3
x = None
try:
    x = int(y)
    f(x)
except:
    logging.error(f"error when x = {x}")
```

This package helps you identify these issues before execution, for example by automatically checking your code in your CI/CD script.

To check your code, install the package and run:

```bash
./check_block_scoping your_dir/*.py
```

or
```
./check_block_scoping your_dir --exclude notthis.py notthat.py
```

This will recursively search `your_dir`.

You can opt-out specific functions and classes by decorating them with `@no_block_scoping`.

Alternatively, you can explicitly opt-in with `@block_scoping`, which removes the need to run `./check_block_scoping` altogether, especially if you want to enforce scoping rules more strictly across your organization, or only at specific locations. 


## Rules

The package implements the following rules:

| Control Flow      | Scope of variables defined inside block                    |
|-------------------|------------------------------------------------------------|
| If/Elif/Else      | block only, unless assigned in all branches                |
| For loop          | block only                                                 |
| While Loop        | block only                                                 |
| Walrus assignment | block only if used in an if or a while                     | 
| `with block_scope()` | block only |
| Other `with` statements | variables outlive their block                              |
| Try/Else/Finally     | Try/Else/Finally: outlive their block but can't be used in Except |
| Except               | block only                                                 |
| Case (Python >= 3.10) | block only                                                |

This applies to:
- all variables,
- all attributes of `self`.

Specifically, you are only allowed to use an attribute of `self` if the attribute is defined in the constructor.

`with` statements do not create block scopes. This is because in 99% of cases, the intent of a `with` statement is for its block to always be executed, unlike if/while/try which are designed for the opposite.

This is why the special object `block_scope` was added.

```python3
with block_scope():
    x = 3
print(x)  # this package counts this as an error
```

## Known Issues

- `./check_block_scoping` is not aware of the variables imported via `from module import *`, potentially raising false positives. The `@block_scoping` decorator doesn't have this issue.

- Except for `self` in classes, `./check_block_scoping` won't detect scoping issues that involve object attributes. 

## External Contribution

Contributions are welcomed!


