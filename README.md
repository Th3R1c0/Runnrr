
## Runnrr — Graph-Based Running Loop Generation with Elevation Optimization

### Overview

**Runnrr** is a Python-based routing system that generates fixed-distance running loops starting and ending at the same location, with an emphasis on minimizing elevation gain. Unlike traditional navigation tools that prioritize point-to-point routing, this project focuses on producing *looped* routes suitable for runners who want a specific distance (e.g., 2 km, 5 km, 10 km) without retracing their steps.

The system models real-world walking networks from OpenStreetMap as weighted graphs and applies classical shortest-path algorithms to search for loops that closely match a target distance while avoiding unnecessary elevation changes.

