import argparse
import os
import ast
import sys
from block_scoping.scoped import _check_class, _check_func, _extract_assign_vars, ImportVisitor

def find_python_files(path, exclude):
    if os.path.isfile(path) and path.endswith('.py'):
        yield path
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            # Remove excluded directories
            dirs = [d for d in dirs if d not in exclude]
            for file in files:
                if file.endswith('.py') and file not in exclude:
                    yield os.path.join(root, file)

def check_file(file_path) -> list:
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read())

    # populate visible scope with top-level imports, assignments, functions and classes
    import_visitor = ImportVisitor()
    import_visitor.visit(tree)
    vars = import_visitor.imports

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            vars.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                vars += _extract_assign_vars(target)

    # check classes and function
    all_errors = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _, errors = _check_func(node, scope_vars=vars, attr_check=False, filename=file_path)
            all_errors += errors
        elif isinstance(node, ast.ClassDef):
            all_errors += _check_class(node, scope_vars=vars, filename=file_path)

    return all_errors


def process_files(file_paths, exclude) -> list:
    errors = []
    for path in file_paths:
        for file_path in find_python_files(path, exclude):
            try:
                errors += check_file(file_path)
            except:
                if len(file_paths) == 1:
                    raise 
                errors += [
                    f"Unrecoverable error while parsing {file_path}. Call the script on this file only to get the details."
                ]

    return errors

def main():
    parser = argparse.ArgumentParser(description="Check Python files for potential bugs.")
    parser.add_argument('paths', nargs='+', help='Python files or directories to check')
    parser.add_argument('--exclude', nargs='*', default=[], 
                        help='File or directory names to exclude')
    parser.add_argument('-q', '--quiet', action='store_true', help="Suppress output")
    
    args = parser.parse_args()
    
    errors = process_files(args.paths, set(args.exclude))
    exit_status = 0
    for err in errors:
        if not args.quiet:
            print(err, file=sys.stderr)
        exit_status = 1

    if len(errors) == 0 and not args.quiet:
        print("No Scoping Issue Found")

    exit(exit_status)

if __name__ == "__main__":
    main()
