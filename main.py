import osmnx as ox
import networkx as nx

#  define location 
START_LAT = 40.768044
START_LON = -73.981893
SEARCH_RADIUS_M = 4500  # 4.5 km radius

def main():
    print("Setting up the project...")
    print(f"Location: {START_LAT}, {START_LON}")
    
    #  Download the walking network from OpenStreetMap
    print("Downloading map data from OSM (this might take a moment)...")
    G = ox.graph_from_point(
        (START_LAT, START_LON),
        dist=SEARCH_RADIUS_M,
        network_type="walk"
    )
    
    # Add edge lengths (important for routing)
    G = ox.distance.add_edge_lengths(G)
    
    print(f"Success! Graph created.")
    print(f"Nodes: {G.number_of_nodes()}")
    print(f"Edges: {G.number_of_edges()}")
    
    #  find the nearest node to our starting point
    start_node = ox.distance.nearest_nodes(G, START_LON, START_LAT)
    print(f"Start Node ID: {start_node}")
    print(f"Start Node Coordinates: {G.nodes[start_node]['y']}, {G.nodes[start_node]['x']}")

if __name__ == "__main__":
    main()
