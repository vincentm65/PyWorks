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
    function_string = None

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            # These will stay at the top when we reconstruct
            import_lines.append(ast.get_source_segment(file_content, node))

        elif isinstance(node, ast.FunctionDef) and node.name == function_name:
            # Extract exact source (including its decorators)
            function_string = ast.get_source_segment(file_content, node)

    if not function_string:
        return ""

    # Combine imports + function cleanly
    combined_code = "\n".join(import_lines + ["", function_string])
    return combined_code

def extract_only_function(new_code: str) -> str:
    lines = new_code.splitlines()
    start = None

    # find the first decorator OR "def"
    for i, line in enumerate(lines):
        striped = line.strip()
        if striped.startswith("@") or striped.startswith("def "):
            start = i
            break

    if start is None:
        return new_code  # fallback

    return "\n".join(lines[start:])


def replace_function_in_file(file_path: Path, function_name: str, new_code: str) -> bool:
    original_content = file_path.read_text(encoding="utf-8")

    try:
        tree = ast.parse(original_content)
    except SyntaxError as e:
        print(f"Syntax error in original file: {e}")
        return False

    target_node = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            target_node = node
            break

    if not target_node:
        print(f"Function '{function_name}' not found in file")
        return False

    start_line = target_node.lineno
    end_line = target_node.end_lineno

    lines = original_content.splitlines(keepends=True)

    # ⬅ Only keep decorators + def, not imports
    function_only = extract_only_function(new_code)

    # Replace exact slice
    new_lines = (
        lines[: start_line - 1]
        + [function_only + ("\n" if not function_only.endswith("\n") else "")]
        + lines[end_line :]
    )

    final_text = "".join(new_lines)
    file_path.write_text(final_text, encoding="utf-8")
    return True

def extract_function_signature(func_node: ast.FunctionDef) -> str:
    func_node_args = []
    for item in func_node.args.args:
        func_node_args.append(item.arg)
    return f"({", ".join(func_node_args)})"

def delete_function_from_file(file_path: Path, function_name: str) -> bool:
    content = file_path.read_text(encoding="utf-8")

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return False

    target = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            target = node
            break

    if not target:
        print(f"Function '{function_name}' not found in {file_path}")
        return False

    start = target.lineno
    end = target.end_lineno

    lines = content.splitlines(keepends=True)

    new_text = "".join(lines[:start - 1] + lines[end:])

    file_path.write_text(new_text, encoding="utf-8")
    return True
