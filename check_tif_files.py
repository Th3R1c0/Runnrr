import rasterio

tifs = [
    "USGS_13_n41w074_20240925.tif",
    "USGS_13_n41w075_20221115.tif",
]

for p in tifs:
    print("\n---", p, "---")
    with rasterio.open(p) as ds:
        print("CRS:", ds.crs)
        print("Res:", ds.res)
        print("Bounds:", ds.bounds)
        print("Nodata:", ds.nodata)
        # Read a tiny window (fast) to confirm file isn't corrupted
        sample = ds.read(1, window=((0, 10), (0, 10)))
        print("Sample OK, shape:", sample.shape)