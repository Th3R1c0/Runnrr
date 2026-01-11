
## Runnrr — Graph-Based Running Loop Generation with Elevation Optimization

### Overview

**Runnrr** is a Python-based routing system that generates fixed-distance running loops starting and ending at the same location, with an emphasis on minimizing elevation gain. Unlike traditional navigation tools that prioritize point-to-point routing, this project focuses on producing *looped* routes suitable for runners who want a specific distance (e.g., 2 km, 5 km, 10 km) without retracing their steps.

The system models real-world walking networks from OpenStreetMap as weighted graphs and applies classical shortest-path algorithms to search for loops that closely match a target distance while avoiding unnecessary elevation changes.

## ⚙️ Highlight: Dijkstra's Algorithm
We use Dijkstra’s Algorithm to find the optimal route.

When finding a "shortest path", "shortest" can mean many things:
- Fewest roads? (unweighted graph)
- Shortest distance? (weight = length)
- Fastest time? (weight = travel_time)
- Least elevation? (weight = grade)

Right now, we are strictly minimizing **distance**. We set `weight="length"`.
The helper function `calculate_path_length` sums the 'length' attribute of every edge traversed in the resulting list of nodes.

Currently, this is just "Point A to Point B". next we will implement a loop and other factors into our code to satisfy requirements.

**The Algorithm:**
1.  **Selection**: Identify `midpoint_node` using `haversine` distance (crow-flies) as a heuristic for road distance.
2.  **Outbound BFS/Dijkstra**: Calculate `out_path` = $Start \to Midpoint$.
3.  **Graph Pruning**: Create a copy of graph `H`. Iterate through edges $(u, v)$ in `out_path` and remove them from `H`. IMPORTANT: We also remove $(v, u)$ to prevent running on the other side of the same street.
4.  **Inbound Search**: Calculate `in_path` = $Midpoint \to Start$ using `H`.
5.  **Merge**: Concatenate lists.

challenges: 
Sometimes, "burning the bridges" traps the runner at the midpoint if the destination is a dead-end (cul-de-sac). We need robust error handling `nx.NetworkXNoPath` to retry with different midpoints if that happens.

