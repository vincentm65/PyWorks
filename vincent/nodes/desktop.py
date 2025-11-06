import sys

def node(func):
    """Decorator to mark a function as a workflow node."""
    func._is_workflow_node = True
    return func

@node
def open_file():
    print('Opening file')