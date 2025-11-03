"""
Example Node Category

Add your @node decorated functions here.
"""

def node(func):
    """Decorator to mark a function as a workflow node."""
    func._is_workflow_node = True
    return func


@node
def example_node(inputs, global_state):
    """
    Example node that demonstrates the basic structure.

    Args:
        inputs: Dictionary of parent node outputs
        global_state: Shared state dictionary

    Returns:
        Dictionary of outputs for child nodes
    """
    print("Example node executed")
    return {"result": "Hello from example node"}


@node
def another_example(inputs, global_state):
    """Another example node."""
    data = inputs.get("example_node", {}).get("result", "")
    print(f"Received: {data}")
    return {"processed": data.upper()}
