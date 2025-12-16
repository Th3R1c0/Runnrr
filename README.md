
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

*currently in progress*