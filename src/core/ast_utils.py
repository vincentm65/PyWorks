import ast
from pathlib import Path
from typing import Dict, Optional, List, Tuple

def has_node_decorator(node: ast.AST, decorator_name: str) -> bool:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return False
    
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == decorator_name:
            return True
        if isinstance(decorator, ast.Attribute) and decorator.attr == decorator_name:
            return True
    return False


def extract_nodes_from_file(file_path: Path, category: str) -> Dict[str, Dict]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
    except OSError as e:
        raise ValueError(f"Failed to read file {file_path}: {e}")

    try:
        tree = ast.parse(file_content)
    except SyntaxError as e:
        raise ValueError(f"Syntax error in {file_path}: {e}")

    nodes: Dict[str, Dict] = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
            
        if has_node_decorator(node, 'node'):
            node_name = node.name
            fqnn = f"{category}.{node_name}"
            
            nodes[fqnn] = {
                'fqnn': fqnn,
                'category': category,
                'function_name': node_name,
                'file_path': file_path,
                'docstring': ast.get_docstring(node),
                'lineno': node.lineno,
                'end_lineno': node.end_lineno
            }

    return nodes


def extract_function_with_imports(file_path: Path, function_name: str) -> Tuple[List[str], str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
    except OSError as e:
        raise ValueError(f"Failed to read file {file_path}: {e}")

    try:
        tree = ast.parse(file_content)
    except SyntaxError as e:
        raise ValueError(f"Syntax error in {file_path}: {e}")

    import_lines = []
    function_code = ""

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_lines.append(ast.get_source_segment(file_content, node))
        elif isinstance(node, ast.FunctionDef) and node.name == function_name:
            function_code = ast.get_source_segment(file_content, node)
            break

    return import_lines, function_code


def replace_function_in_file(file_path: Path, function_name: str, new_code: str) -> bool:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except OSError as e:
        raise ValueError(f"Failed to read file {file_path}: {e}")

    try:
        original_tree = ast.parse(original_content)
    except SyntaxError as e:
        raise ValueError(f"Syntax error in {file_path}: {e}")

    # Parse new code
    try:
        new_tree = ast.parse(new_code)
    except SyntaxError as e:
        raise ValueError(f"Syntax error in new code: {e}")

    # Find target function in original tree
    target_function = None
    for node in original_tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            target_function = node
            break

    if not target_function:
        raise ValueError(f"Function '{function_name}' not found in file")

    # Replace function with new code
    new_body = []
    for node in original_tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            new_body.append(target_function)
        else:
            new_body.append(node)

    # Update AST and write back
    original_tree.body = new_body
    new_source = ast.unparse(original_tree)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_source)
    except OSError as e:
        raise ValueError(f"Failed to write to {file_path}: {e}")

    return True
