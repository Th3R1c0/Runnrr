import osmnx as ox
import networkx as nx

START_LAT = 40.768044
START_LON = -73.981893
SEARCH_RADIUS_M = 4500

def main():
    # Setup graph 
    print("Loading graph...")
    G = ox.graph_from_point((START_LAT, START_LON), dist=SEARCH_RADIUS_M, network_type="walk")
    G = ox.distance.add_edge_lengths(G)
    
    start_node = ox.distance.nearest_nodes(G, START_LON, START_LAT)
    
    #  pick a random destination node just to test 
    import random
    dest_node = random.choice(list(G.nodes()))
    
    print(f"Routing from {start_node} to {dest_node}...")
    
    try:
        # shortest path using Dijkstra's Algorithm
        # weight="length" implies we want the physically shortest route not just fewest turns
        path = nx.shortest_path(G, start_node, dest_node, weight="length")
        
        # Calculate total distance
        distance = calculate_path_length(G, path)
        print(f"Path found! It involves {len(path)} steps.")
        print(f"Total distance: {distance:.2f} meters")
        
    except nx.NetworkXNoPath:
        print("No path found (destination might be on an island or disconnected subgraph).")

def calculate_path_length(G, path):
    total_len = 0.0
    # Iterate through pairs of nodes in the path: (0,1), (1,2), (2,3)...
    for u, v in zip(path[:-1], path[1:]):
        # in a MultiDiGraph, there might be multiple edges between u and v.
        # We take the one with the minimum length just to be safe :)
        edge_data = G[u][v][0] 
        total_len += edge_data['length']
    return total_len

if __name__ == "__main__":
    main()
