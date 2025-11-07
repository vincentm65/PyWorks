from .node_registry import NodeRegistry
from .topological import topological_sort

class GraphBuilder:
    def __init__(self, layout_data: dict, node_registry):
        self.layout_data = layout_data
        self.node_registry = node_registry

        self.all_nodes = set()
        self.flow_graph = {}
        self.data_graph = {}

    def build(self):
        self._extract_nodes()
        self._build_flow_graph()
        self._build_data_graph()
        self._validate()
        return self

    def _extract_nodes(self):
        nodes_dict = self.layout_data.get('nodes', {})
        self.all_nodes = set(nodes_dict.keys())

    def _build_flow_graph(self):
        self.flow_graph = {node: [] for node in self.all_nodes}
        connections = self.layout_data.get('connections', [])

        for conn in connections:
            if conn['source_port_type'] == 'FLOW':
                from_node = conn['source_node_key']
                to_node = conn['target_node_key']
                self.flow_graph[from_node].append(to_node)

    def _build_data_graph(self):
        self.data_graph = {node: [] for node in self.all_nodes}
        connections = self.layout_data.get('connections', [])

        for conn in connections:
            if conn['source_port_type'] == 'DATA':
                from_node = conn['source_node_key']
                to_node = conn['target_node_key']
                self.data_graph[to_node].append((from_node, 'output_data'))


    def _validate(self):
        for node_key in self.all_nodes:
            parts = node_key.rsplit('_', 2)
            fqnn = parts[0]
        
            if not self.node_registry.get_metadata(fqnn):
                raise ValueError(f"Node '{fqnn}' not found in registry.")

    def has_cycle(self) -> bool:
        try:
            topological_sort(self.flow_graph, self.all_nodes)
            return False
        except ValueError:
            return True

    def get_entry_nodes(self) -> list:
        in_degree = {node: 0 for node in self.all_nodes}

        for node in self.all_nodes:
            for child in self.flow_graph.get(node, []):
                in_degree[child] += 1

        entry_nodes = [node for node in self.all_nodes if in_degree[node] == 0]
        return entry_nodes
