import sys
import json
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsItem, QStyle
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
                node_title = item.title
                node_x = item.pos().x()
                node_y = item.pos().y()

                node_key = f"{node_title}_{int(node_x)}_{int(node_y)}"

                layout_data["nodes"][node_key] = {"x": node_x, "y": node_y}

        for connection in scene.connections:
            source_node = connection.source_port.parent_node
            source_title = source_node.title
            source_type = connection.source_port.port_type
            source_dir = connection.source_port.port_direction
            source_x = int(source_node.pos().x())
            source_y = int(source_node.pos().y())
            source_key = f"{source_title}_{source_x}_{source_y}"

            target_node = connection.target_port.parent_node
            target_title = target_node.title
            target_type = connection.target_port.port_type
            target_dir = connection.target_port.port_direction
            target_x = int(target_node.pos().x())
            target_y = int(target_node.pos().y())
            target_key = f"{target_title}_{target_x}_{target_y}"

            connection_data = {
                "source_node_key": source_key,
                "source_port_type": source_type,
                "source_port_direction": source_dir,
                "target_node_key": target_key,
                "target_port_type": target_type,
                "target_port_direction": target_dir
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

        for node_key, position, in layout_data["nodes"].items():
            part = node_key.rsplit('_', 2)
            node_title = part[0]

            x = position["x"]
            y = position["y"]

            node = NodeItem(node_title, x, y)
            scene.addItem(node)
            node_dict[node_key] = node

        source_port = None

        for connection_data in layout_data['connections']:
            source_node_name = connection_data["source_node_key"]
            target_node_name = connection_data["target_node_key"]

            source_node = node_dict.get(source_node_name)
            target_node = node_dict.get(target_node_name)

            if source_node is None:
                print(f"Warning: Source node '{source_node_name}' not found. Skipping connection.")
                continue
            if target_node is None:
                print(f"Warning: Target node '{target_node_name}' not found. Skipping connection.")
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
