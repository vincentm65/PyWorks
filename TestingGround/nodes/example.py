import sys
import time
'\nExample Node Category\n\nAdd your @node decorated functions here.\n'

def node(func):
    """Decorator to mark a function as a workflow node."""
    func._is_workflow_node = True
    return func

@node
def send_local_example(inputs, global_state):
    message = 'Hello World'
    time.sleep(1)

    # We return "results" in this case as our key, that has message as our value.
    return {'result': message} 

@node
def receive_local_example(inputs, global_state):
    # Below are all our of inputs we received as an argument
    print(f'All inputs {inputs}')

    time.sleep(1)

    # We can get specific inputs with .get().
    data = inputs.get('example.send_local_example', {}).get('result', '')

    # Printing the data we got from the results of send_local_example
    print(f'Received: {data} from parent node')

    # No need for a return sice we are only receiving in this function.
    return {}

@node
def create_global_example(inputs, global_state):

    # Here we set a standard variable
    this_is_global = "Global variable all nodes can read!"
    import_text = input("Enter text: ")
    # Then it is made global by assingning it a new value in the global state dict. Now all nodes can access it.
    global_state["Test_Global"] = import_text
    time.sleep(1)

    # No need to return anything
    return {} 

@node
def receive_global_example(inputs, global_state):

    # Print out the global state, this will print anywhere after the global
    print(global_state["Test_Global"])
    time.sleep(1)
    
    # No need to return
    return {}