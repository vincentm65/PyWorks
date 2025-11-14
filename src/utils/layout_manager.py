import json
from PyQt6.QtWidgets import QGraphicsItem, QStyle
from PyQt6.QtCore import QRectF, QPointF, Qt

from ui.nodes.node_item import NodeItem
from ui.nodes.connection_item import ConnectionBridge


class LayoutManager():
    def __init__(self, parent = None):
        pass

    def save_layout(self, scene, file_path):
        # Get all node and bridge data
        layout_data = {
            "version": "1.0",
            "nodes" : {},
            "connections": []
        }

        for item in scene.items():
            if isinstance(item, NodeItem):
                layout_data["nodes"][item.id] = {
                    "fqnn": item.fqnn,
                    "x": item.pos().x(), 
                    "y": item.pos().y()
                    }

        for connection in scene.connections:
            source_node_id = connection.source_port.parent_node.id
            target_node_id = connection.target_port.parent_node.id

            connection_data = {
                "source_node_id": source_node_id,
                "source_port_type": connection.source_port.port_type,
                "source_port_direction": connection.source_port.port_direction,
                "target_node_id": target_node_id,
                "target_port_type": connection.target_port.port_type,
                "target_port_direction": connection.target_port.port_direction
            }

            layout_data["connections"].append(connection_data)
            
        try:
            with open(file_path, 'w') as f:
                    json.dump(layout_data, f, indent = 2)
                    return True
        except Exception as e:
            print(f"Error saving layout: {e}")
            return False
        
    def load_layout(self, scene, file_path):
        try:
            with open(file_path, 'r') as f:
                print(f"Layout file found: {file_path}")
                layout_data = json.load(f)
        except FileNotFoundError:
            # Handle: file doesn't exist
            print(f"Layout file not found: {file_path}")
            return False
        except json.JSONDecodeError:
            # Handle: file exists but has bad JSON
            print(f"Error parsing layout file: {file_path}")
            return False
        
        node_dict ={}

        for node_id, node_data in layout_data["nodes"].items():
            # Backward compatibility for old layout files
            if "fqnn" in node_data:
                fqnn = node_data["fqnn"]
            else:
                # Old format used category and function to build fqnn
                fqnn = f"{node_data['category']}.{node_data['function']}"

            x = node_data["x"]
            y = node_data["y"]

            node = NodeItem(fqnn, x, y, id=node_id)
            scene.addItem(node)
            node_dict[node_id] = node

        source_port = None

        for connection_data in layout_data['connections']:
            # Backward compatibility for old connection keys
            source_node_id = connection_data.get("source_node_id") or connection_data.get("source_node_key")
            target_node_id = connection_data.get("target_node_id") or connection_data.get("target_node_key")

            source_node = node_dict.get(source_node_id)
            target_node = node_dict.get(target_node_id)

            if source_node is None:
                print(f"Warning: Source node '{source_node_id}' not found. Skipping connection.")
                continue
            if target_node is None:
                print(f"Warning: Target node '{target_node_id}' not found. Skipping connection.")
                continue

            source_port = None
            for port in source_node.ports:
                if port.port_type == connection_data["source_port_type"] and port.port_direction == connection_data["source_port_direction"]:
                    source_port = port
                    break

            target_port = None
            for port in target_node.ports:
                if port.port_type == connection_data["target_port_type"] and port.port_direction == connection_data["target_port_direction"]:
                    target_port = port
                    break

            if source_port is None:
                print(f"Warning: Source port not found for connection. Skipping.")
                continue
            if target_port is None:
                print(f"Warning: Target port not found for connection. Skipping.")
                continue

            connection = ConnectionBridge(source_port, target_port)
            scene.addItem(connection)
            scene.connections.append(connection)

        return True
