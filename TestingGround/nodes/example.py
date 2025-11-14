import sys
import time
'\nExample Node Category\n\nAdd your @node decorated functions here.\n'

def node(func):
    """Decorator to mark a function as a workflow node."""
    func._is_workflow_node = True
    return func

@node
def send_example(inputs, global_state):
    """
    Example node that demonstrates the basic structure.

    Args:
        inputs: Dictionary of parent node outputs
        global_state: Shared state dictionary

    Returns:
        Dictionary of outputs for child nodes
    """
    time.sleep(1)
    message = 'Hello World!'
    return {'result': message}

@node
def receive_example(inputs, global_state):
    print(f'All inputs {inputs}')
    time.sleep(1)
    data = inputs.get('example.send_example', {}).get('result', '')
    print(f'Received: {data} from parent node')
    return {'processed': data.upper()}