import sys
import yaml
from index_node import IndexNode

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <node_id>")
        sys.exit(1)
    
    node_id = sys.argv[1]
    
    with open("config/cluster.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    node_config = None
    for node in config["nodes"]:
        if node["id"] == node_id:
            node_config = node
            break
    
    if not node_config:
        print(f"Node {node_id} not found in configuration")
        sys.exit(1)
    
    node = IndexNode(node_id, node_config["port"])
    print(f"Starting index node {node_id} on port {node_config['port']}")
    node.start()

if __name__ == "__main__":
    main()
