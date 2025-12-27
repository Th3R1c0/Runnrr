import osmnx as ox
import networkx as nx
import math
import random

START_LAT = 40.768044
START_LON = -73.981893
SEARCH_RADIUS_M = 4500
TARGET_LOOP_M = 5000  #  5km run

def haversine_m(lat1, lon1, lat2, lon2):
    # calculates distance between two points on earth, good little function
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_loop(G, start_node, target_distance):
    # 1. Select a mdpoint"roughly halfway out
    # and if we want 5km total we need a point ~2.5km away (graph distance), 
    # but straight line distance is usually shorter
    
    midpoint_target_dist = target_distance / 4  # Pure heuristic
    candidates = []
    
    lat0 = G.nodes[start_node]["y"]
    lon0 = G.nodes[start_node]["x"]
    
    for n, data in G.nodes(data=True):
        dist = haversine_m(lat0, lon0, data["y"], data["x"])
        # pick points in a "ring" around the start
        if abs(dist - midpoint_target_dist) < 200: 
            candidates.append(n)
            
    if not candidates:
        print("No suitable midpoints found.")
        return None

    mid_node = random.choice(candidates)
    
    #  route outbound
    try:
        out_path = nx.shortest_path(G, start_node, mid_node, weight="length")
    except nx.NetworkXNoPath:
        return None

    #  remove used edges to force a different path back
    H = G.copy()
    for u, v in zip(out_path[:-1], out_path[1:]):
        if H.has_edge(u, v):
            H.remove_edge(u, v)
        # also remove reverse direction if it exists (don't run on same street opposite way)
        if H.has_edge(v, u):
            H.remove_edge(v, u)
            
    #  route Inbound
    try:
        in_path = nx.shortest_path(H, mid_node, start_node, weight="length")
    except nx.NetworkXNoPath:
        print("Could not find a way back without retracing steps!")
        return None
        
    full_loop = out_path + in_path[1:]
    return full_loop

def main():
    print("Loading Graph...")
    G = ox.graph_from_point((START_LAT, START_LON), dist=SEARCH_RADIUS_M, network_type="walk")
    G = ox.distance.add_edge_lengths(G)
    start_node = ox.distance.nearest_nodes(G, START_LON, START_LAT)
    
    print(f"Attempting to find a {TARGET_LOOP_M}m loop...")
    loop = get_loop(G, start_node, TARGET_LOOP_M)
    
    if loop:
        length = sum(ox.utils_graph.get_route_edge_attributes(G, loop, "length"))
        print(f"Loop found! Total Length: {length:.2f} meters")
        print(f"Nodes in path: {len(loop)}")
    else:
        print("Failed to generate a valid loop.")

if __name__ == "__main__":
    main()
