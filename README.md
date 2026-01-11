
## Runnrr — Graph-Based Running Loop Generation with Elevation Optimization

### Overview

**Runnrr** is a Python-based routing system that generates fixed-distance running loops starting and ending at the same location, with an emphasis on minimizing elevation gain. Unlike traditional navigation tools that prioritize point-to-point routing, this project focuses on producing *looped* routes suitable for runners who want a specific distance (e.g., 2 km, 5 km, 10 km) without retracing their steps.

The system models real-world walking networks from OpenStreetMap as weighted graphs and applies classical shortest-path algorithms to search for loops that closely match a target distance while avoiding unnecessary elevation changes.

---

### Graph Modeling

The routing graph is constructed using OSMnx and NetworkX:

* Each edge is weighted by distance (meters).
* Elevation values are sampled from the DEM and attached to every node.
* Elevation gain is computed by summing positive elevation differences along a path.

This enables the system to reason about both **distance** and **terrain** when evaluating candidate routes.

---

### Algorithmic Approach

#### 1. Single-Source Shortest Path Precomputation

The system begins by running **single-source Dijkstra** from the start node. This produces:

* the shortest distance from the start to every reachable node
* the corresponding shortest paths

This step is performed once to avoid repeated expensive computations.

#### 2. Ring-Based Midpoint Sampling

Instead of searching the entire graph, candidate midpoints are sampled from a *distance-based ring* centered on the start location. Nodes are selected whose straight-line distance lies near half the target route length. This biases the search toward roughly circular loops and reduces the search space dramatically.

#### 3. Loop Construction with Edge Reuse Constraints

For each candidate midpoint:

* the outbound path is taken from the precomputed Dijkstra results
* a return path is computed using **A*** search
* edges used in the outbound path are removed before computing the return path, ensuring the loop is not simply an out-and-back route

#### 4. Scoring and Selection

Each valid loop is evaluated using a scoring function that balances:

* distance error from the target length
* total elevation gain (weighted)

The best-scoring loop found within a fixed time limit is selected.

---

### Performance Considerations

Several design choices were made to keep the system responsive on large city graphs:

* single-source shortest-path precomputation
* midpoint ring sampling instead of brute-force search
* hard time limits on loop search
* limiting candidate counts

These allow the system to operate on graphs with tens of thousands of nodes in seconds.

---

### Output

The final route is exported as a **GeoJSON LineString**, making it easy to:

* visualize in tools like geojson.io
* integrate into mapping applications
* extend into a frontend or mobile app

Each output includes metadata such as:

* total distance
* distance error
* elevation gain

---

## 📦 Installation & Setup

### Prerequisites
- Python 3.8+
- Use the provided header in `main.py` to install dependencies:

```bash
pip install osmnx networkx geopandas shapely pyproj scikit-learn rasterio numpy requests
```

### Data Setup
To run the code, you need:
1.  **The Code:** `main.py`.
2.  **Elevation Data:** A merged functionality GeoTIFF file (referenced as `merged_files.tif` in the code) containing the DEM data for your area of interest. *Note: The repository currently contains source .tif files; ensure these are merged or the script configuration points to the correct elevation file.*

---

## 🚀 Usage

1.  **Configure the Script:**
    Open `main.py` and adjust the configuration block at the top:
    ```python
    START_LAT = 40.768044   # Your starting latitude
    START_LON = -73.981893  # Your starting longitude
    TARGET_M = 2000         # Target distance in meters (e.g., 2km)
    TOL_M = 120             # Allowed deviation (e.g., +/- 120m)
    MERGED_DEM_PATH = "merged_files.tif" # Path to your DEM file
    ```

2.  **Run the Script:**
    ```bash
    python main.py
    ```

3.  **View Results:**
    - The script will print the loop details (Length, Error, Climb).
    - A file named `loop_2k_nyc_dem.geojson` (or your configured name) will be generated.
    - Drag and drop this file into [geojson.io](https://geojson.io) to see your route on a map!

---

## 🧩 Technical Stack

-   **Language:** Python
-   **Graph Utilities:** NetworkX, OSMnx
-   **Geospatial Data:** GDAL/Rasterio (for DEM processing), GeoPandas
-   **Algorithms:** Dijkstra, A* (A-Star), Heuristic Optimization

---

## 🔮 Future Improvements

-   **Web Interface:** Build a frontend to allow users to click a start point on a map.
-   **Surface Preference:** avoiding busy roads or prioritizing parks.
-   **Heatmaps:** showing popular running routes overlay.
-   **Dynamic Tiling:** Automatically downloading DEM tiles based on the requested location instead of requiring local files.

---