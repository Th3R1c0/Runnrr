pip install osmnx networkx geopandas shapely pyproj scikit-learn rasterio numpy requests

import os
import time
import json
import math
import random

import numpy as np
import rasterio
from rasterio.warp import transform as rio_transform
from rasterio.transform import rowcol

import osmnx as ox
import networkx as nx



# CONFIG

START_LAT = 40.768044
START_LON = -73.981893

TARGET_M = 2000
TOL_M = 120

SEARCH_RADIUS_M = 4500
TIME_LIMIT_SEC = 10

# ring midpoint sampling 
RING_CENTER_M = TARGET_M / 2
RING_WIDTH_M = 250
MAX_RING_CANDIDATES = 800

# outbound distance window 
MIDPOINT_MIN_M = 650
MIDPOINT_MAX_M = 1350

FORBID_REUSE_UNDIRECTED = True

# Elevation scoring 
ELEV_WEIGHT = 2.0


MERGED_DEM_PATH = "merged_files.tif"

EXPORT_FILE = "loop_2k_nyc_dem.geojson"





def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def ring_midpoint_candidates(G, start_node):
    lat0 = G.nodes[start_node]["y"]
    lon0 = G.nodes[start_node]["x"]
    ring = []
    for n, data in G.nodes(data=True):
        d = haversine_m(lat0, lon0, data["y"], data["x"])
        if abs(d - RING_CENTER_M) <= RING_WIDTH_M:
            ring.append(n)
    random.shuffle(ring)
    return ring[:min(MAX_RING_CANDIDATES, len(ring))]



# DEM sampling :)

class DemSampler:
    """
    Samples elevation from a DEM GeoTIFF.
    Handles CRS mismatch by transforming WGS84 lon/lat into DEM CRS before sampling.
    """
    def __init__(self, dem_path: str):
        self.dem_path = dem_path
        self.ds = rasterio.open(dem_path)
        self.band = self.ds.read(1)
        self.nodata = self.ds.nodata
        self.crs = self.ds.crs

    def close(self):
        self.ds.close()

    def elevation_at_lonlat(self, lon: float, lat: float):
        # Transform (lon,lat) from EPSG:4326 to DEM CRS if needed
        if self.crs is not None and str(self.crs).lower() not in ("epsg:4326", "wgs84"):
            xs, ys = rio_transform("EPSG:4326", self.crs, [lon], [lat])
            x, y = xs[0], ys[0]
        else:
            x, y = lon, lat

        try:
            r, c = rowcol(self.ds.transform, x, y)
            if not (0 <= r < self.band.shape[0] and 0 <= c < self.band.shape[1]):
                return None
            val = self.band[r, c]
            if self.nodata is not None and val == self.nodata:
                return None
            if isinstance(val, (np.integer, np.floating)) and (val < -1000 or val > 10000):
                return None
            return float(val)
        except Exception:
            return None


def attach_dem_elevation(G, dem_path):
    sampler = DemSampler(dem_path)
    missing = 0

    for n, data in G.nodes(data=True):
        lon = data["x"]
        lat = data["y"]
        elev = sampler.elevation_at_lonlat(lon, lat)
        if elev is None:
            missing += 1
            elev = 0.0
        G.nodes[n]["elev"] = elev

    sampler.close()
    print(f"Elevation attached. Missing filled with 0: {missing} / {G.number_of_nodes()}")


def elevation_gain_m(G, path):
    gain = 0.0
    for u, v in zip(path[:-1], path[1:]):
        du = G.nodes[u]["elev"]
        dv = G.nodes[v]["elev"]
        if dv > du:
            gain += (dv - du)
    return gain



# som routing helpers

def path_length_m(G, path):
    return sum(G[u][v][0]["length"] for u, v in zip(path[:-1], path[1:]))


def remove_used_edges(G, path):
    H = G.copy()
    used = set(zip(path[:-1], path[1:]))

    if FORBID_REUSE_UNDIRECTED:
        used |= {(v, u) for (u, v) in used}

    for u, v in used:
        if H.has_edge(u, v):
            for k in list(H[u][v].keys()):
                H.remove_edge(u, v, k)
    return H



# main

def main():
    # 1) require the merged graph 
    if not os.path.exists(MERGED_DEM_PATH):
        raise FileNotFoundError(
            f"Missing DEM file: {MERGED_DEM_PATH}\n"
            "Make sure merged_files.tif is in the same folder as this script."
        )
    dem_path = MERGED_DEM_PATH
    print(f"Using DEM: {dem_path}")

    # 2) Load my osm graph
    print("Loading OSM walk graph...")
    G = ox.graph_from_point(
        (START_LAT, START_LON),
        dist=SEARCH_RADIUS_M,
        network_type="walk",
    )
    G = ox.distance.add_edge_lengths(G)
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # 3) Snap start
    start_node = ox.distance.nearest_nodes(G, START_LON, START_LAT)
    print("Snapped start:", G.nodes[start_node]["y"], G.nodes[start_node]["x"])

    # 4) Attach DEM elevations 
    attach_dem_elevation(G, dem_path)

    # 5) Precompute Dijkstra once 
    print("Precomputing distances from start (single Dijkstra)...")
    dist_from_start, paths_from_start = nx.single_source_dijkstra(G, start_node, weight="length")
    print("Done.")

    # 6) Ring sampling candidates
    candidates = ring_midpoint_candidates(G, start_node)
    print(f"Ring midpoint candidates: {len(candidates)}")

    # 7) Search loops
    best = None
    t0 = time.time()
    print("Searching for loop...")

    for mid in candidates:
        if time.time() - t0 > TIME_LIMIT_SEC:
            print("Time limit reached.")
            break

        if mid not in dist_from_start:
            continue

        out_len = dist_from_start[mid]
        if not (MIDPOINT_MIN_M <= out_len <= MIDPOINT_MAX_M):
            continue

        out_path = paths_from_start[mid]

        try:
            H = remove_used_edges(G, out_path)
            back_path = nx.astar_path(H, mid, start_node, weight="length")
            back_len = path_length_m(G, back_path)
        except nx.NetworkXNoPath:
            continue

        loop_len = out_len + back_len
        err = abs(loop_len - TARGET_M)
        if err > TOL_M:
            continue

        loop_path = out_path + back_path[1:]
        if loop_path[0] != start_node or loop_path[-1] != start_node:
            continue

        gain = elevation_gain_m(G, loop_path)

      
        score = err + ELEV_WEIGHT * gain

        if best is None or score < best[0]:
            best = (score, err, loop_len, gain, loop_path)

        if err <= 20:
            break

    if best is None:
        print("No loop found. Try:")
        print("- Increase SEARCH_RADIUS_M (6000–8000)")
        print("- Increase RING_WIDTH_M (500–800)")
        print("- Increase TOL_M (150–250)")
        return

    score, err, loop_len, gain, loop_path = best
    print("Loop found!")
    print(f"Length: {loop_len:.1f} m | error: {err:.1f} m | climb: {gain:.1f} m | score: {score:.1f}")

    # 8) Export GeoJSON single LineString (lon,lat) for geojson.io
    coords = [(G.nodes[n]["x"], G.nodes[n]["y"]) for n in loop_path]
    if coords[0] != coords[-1]:
        coords.append(coords[0])

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "target_m": TARGET_M,
                    "length_m": loop_len,
                    "error_m": err,
                    "elevation_gain_m": gain,
                },
                "geometry": {"type": "LineString", "coordinates": coords},
            }
        ],
    }

    with open(EXPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(geojson, f)

    print(f"Saved → {EXPORT_FILE}")


if __name__ == "__main__":
    main()
