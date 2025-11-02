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
            function_lines.append(ast.get_source_segment(file_content, node))

    if not function_lines:
        return ""

    combined_code = '\n'.join(import_lines + [''] + function_lines)
    return combined_code
