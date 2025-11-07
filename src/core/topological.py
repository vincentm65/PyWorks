
def topological_sort(flow_graph: dict, all_nodes: set) -> list:
    # Step 1: Calculate in-degree for each node
    in_degree = {}
    for node in all_nodes:
        in_degree[node] = 0

    for node in all_nodes:
        children = flow_graph.get(node, [])

        for child in children:
            in_degree[child] += 1
        
    # Step 2: Find all starting nodes (in-degree == 0)
    queue = []

    for node in all_nodes:
        if in_degree[node] == 0:
            queue.append(node)

    sorted_order = []

    # Step 3: Process nodes using queue
    while len(queue) > 0:
        node = queue.pop(0)

        sorted_order.append(node)
        children = flow_graph.get(node, [])
        for child in children:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)
        

    # Step 4: Check if all nodes were processed (detect cycles)
    if len(sorted_order) != len(all_nodes):
        raise ValueError("Cycle detected in FLOW graph.")

    return sorted_order