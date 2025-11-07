import ast
from pathlib import Path

# Check if a given AST node has a specific decorator
def has_node_decorator(node, decorator_name):
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return False
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == decorator_name:
            return True
        if isinstance(decorator, ast.Attribute) and decorator.attr == decorator_name:
            return True
    return False


# Parse a python file and return all @node decorated functions as a dictionary
def extract_nodes_from_file(file_path: Path, category: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()

    try:
        tree = ast.parse(file_content)
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return {}

    nodes = {}

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and has_node_decorator(node, 'node'):
            node_name = node.name
            fqnn = f'{category}.{node_name}'
            nodes[fqnn] = {
                'fqnn': fqnn,
                'category': category,
                'function_name': node.name,
                'signature': extract_function_signature(node),
                'file_path': file_path,
                'docstring': ast.get_docstring(node),
                'lineno': node.lineno,
                'end_lineno': node.end_lineno
            }

    return nodes

# Get the imports then get the specific funtion, combine them into a single string
def extract_function_with_imports(file_path: Path, function_name: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()

    try:
        tree = ast.parse(file_content)
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return ""

    import_lines = []
    function_lines = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_lines.append(ast.get_source_segment(file_content, node))
        elif isinstance(node, ast.FunctionDef) and node.name == function_name:
            decorator_lines = []
            for decorator in node.decorator_list:
                decorator_segment = ast.get_source_segment(file_content, decorator)
                decorator_lines.append(f"@{decorator_segment}")
            
            function_segment = ast.get_source_segment(file_content, node)

            full_function = (
                '\n'.join(decorator_lines) + '\n' + function_segment
                if decorator_lines
                else function_segment
            )

            function_lines.append(full_function)

    if not function_lines:
        return ""

    combined_code = '\n'.join(import_lines + [''] + function_lines)
    return combined_code

def replace_function_in_file(file_path: Path, function_name: str, new_code: str) -> bool:
    with open(file_path, 'r', encoding='utf-8') as f:
        original_content = f.read()

    try:
        original_tree = ast.parse(original_content)
        new_tree = ast.parse(new_code)
    except SyntaxError as e:
        print(f"Syntax error: {e}")
        return False
    
    new_imports = []
    new_function = None

    for node in new_tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            new_imports.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name == function_name:
            new_function = node
    
    if not new_function:
          print(f"Function '{function_name}' not found in new code")
          return False

    # Merge imports and replace function in original tree
    function_replaced = False
    new_body = []

    new_body.extend(new_imports)

    for node in original_tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            # Track existing imports to avoid duplicates
            continue
        elif isinstance(node, ast.FunctionDef) and node.name == function_name:
            # Replace the target function
            new_body.append(new_function)
            function_replaced = True
        else:
            # Keep everything else (other functions, classes, etc.)
            new_body.append(node)

    if not function_replaced:
        print(f"Function '{function_name}' not found in original file")
        return False

    # Generate new source code
    original_tree.body = new_body
    new_source = ast.unparse(original_tree)

    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_source)

    return True

def extract_function_signature(func_node: ast.FunctionDef) -> str:
    func_node_args = []
    for item in func_node.args.args:
        func_node_args.append(item.arg)
    return f"({", ".join(func_node_args)})"
