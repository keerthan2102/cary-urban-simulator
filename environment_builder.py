import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import box

def build_ultimate_environment(grid_size=120):
    print(" Connecting to Cary Open Data Infrastructure API...")
    
    # 1. Official Live OpenDataSoft API GeoJSON Endpoints
    boundary_url = "https://data.townofcary.org/api/v2/catalog/datasets/cary-corporate-limits/exports/geojson"
    parks_url = "https://data.townofcary.org/api/v2/catalog/datasets/parks-and-recreation-feature-polygons/exports/geojson"
    housing_url = "https://data.townofcary.org/api/v2/catalog/datasets/residential-boundaries/exports/geojson"
    roads_url = "https://data.townofcary.org/api/v2/catalog/datasets/streets/exports/geojson"
    
    print(" Ingesting transportation, park, and neighborhood layers...")
    try:
        cary_gdf = gpd.read_file(boundary_url).to_crs(epsg=2264)
        parks_gdf = gpd.read_file(parks_url).to_crs(epsg=2264)
        housing_gdf = gpd.read_file(housing_url).to_crs(epsg=2264)
        all_roads_gdf = gpd.read_file(roads_url).to_crs(epsg=2264)
        print(" Data layers successfully downloaded via stream.")
    except Exception as e:
        print(f" Network Ingestion Pipeline Error: {e}")
        return

    # 2. Filter Street Network down to Major Commuter Arterials & Freeways
    # Cary classifies primary infrastructure routes under the 'thoroughfar' structural key
    if 'thoroughfar' in all_roads_gdf.columns:
        highways_gdf = all_roads_gdf[all_roads_gdf['thoroughfar'].astype(str).str.lower().str.contains('thoroughfare|freeway', na=False)]
    else:
        # Fallback contingency in case of column schema renames
        print(" 'thoroughfar' column not explicitly found. Scanning alternative structural names...")
        possible_cols = [col for col in all_roads_gdf.columns if 'class' in col.lower() or 'type' in col.lower() or 'road' in col.lower()]
        if possible_cols:
            highways_gdf = all_roads_gdf[all_roads_gdf[possible_cols[0]].astype(str).str.lower().str.contains('arterial|highway|major', na=False)]
        else:
            highways_gdf = all_roads_gdf

    print(f" Isolated {len(highways_gdf)} primary transit corridor segments.")

    # 3. Spatial Intersection Clipping
    print(" Clipping global geospatial assets to municipal borders...")
    cary_parks = gpd.clip(parks_gdf, cary_gdf)
    cary_housing = gpd.clip(housing_gdf, cary_gdf)
    cary_highways = gpd.clip(highways_gdf, cary_gdf)
    
    # 4. Grid Coordinate Translation Computations
    bounds = cary_gdf.total_bounds # minx, miny, maxx, maxy
    minx, miny, maxx, maxy = bounds
    x_step = (maxx - minx) / grid_size
    y_step = (maxy - miny) / grid_size
    
    # Layer 1: Zoning Grid (0=Void, 1=Open Developable Space, 2=Pre-Existing Neighborhood, 5=Park)
    zone_matrix = np.zeros((grid_size, grid_size), dtype=int)
    # Layer 2: Proximity Buffering (Tracks distance offset to nearest highway line in cell units)
    highway_matrix = np.ones((grid_size, grid_size)) * 999
    
    # Collapse geometries into unary shapes for lightning-fast vectorized predicates
    cary_polygon = cary_gdf.geometry.unary_union
    parks_polygon = cary_parks.geometry.unary_union
    housing_polygon = cary_housing.geometry.unary_union
    highways_geometry = cary_highways.geometry.unary_union
    
    # Unpack line geometries into raw coordinate coordinate arrays for vectorized distance calculations
    highway_nodes = []
    if hasattr(highways_geometry, 'geoms'): # MultiLineString
        for line in highways_geometry.geoms:
            highway_nodes.extend(line.coords)
    elif hasattr(highways_geometry, 'coords'): # LineString
        highway_nodes.extend(highways_geometry.coords)
        
    highway_nodes = np.array(highway_nodes)

    print(" Processing multi-layer spatial matrix grids...")
    for grid_y in range(grid_size):
        for grid_x in range(grid_size):
            # Calculate physical geometric midpoint of target pixel cell
            cell_x = minx + (grid_x * x_step) + (x_step / 2)
            cell_y = miny + (grid_y * y_step) + (y_step / 2)
            cell_poly = box(cell_x - x_step/2, cell_y - y_step/2, cell_x + x_step/2, cell_y + y_step/2)
            
            # Execute topological predicates
            if cell_poly.intersects(cary_polygon):
                if cell_poly.intersects(parks_polygon):
                    zone_matrix[grid_y][grid_x] = 5  # Protected Nature Asset
                elif cell_poly.intersects(housing_polygon):
                    zone_matrix[grid_y][grid_x] = 2  # Baseline Existing Assets
                else:
                    zone_matrix[grid_y][grid_x] = 1  # Open Canopy Space
                
                # Proximity Math: Euclidean optimization distance mapping
                if len(highway_nodes) > 0:
                    dists = np.sqrt((highway_nodes[:, 0] - cell_x)**2 + (highway_nodes[:, 1] - cell_y)**2)
                    # Convert absolute physical feet to scalar grid-step metrics
                    highway_matrix[grid_y][grid_x] = np.min(dists) / ((x_step + y_step) / 2)
            else:
                zone_matrix[grid_y][grid_x] = 0  # Extrajurisdictional Void Space

    # 5. Serialization and Verification Plots
    np.save("real_cary_matrix.npy", zone_matrix)
    np.save("real_cary_highways.npy", highway_matrix)
    print(" Twin-layer infrastructure arrays serialized successfully!")

    # Verify the highway distance field looks smooth and accurate
    plt.figure(figsize=(9, 7))
    plt.imshow(highway_matrix, origin="lower", cmap="plasma_r", vmin=0, vmax=30)
    plt.title("Infrastructure Vector Check: Highway Proximity Fields")
    plt.colorbar(label="Grid Distance Steps to Closest Corridor")
    plt.savefig("highway_distance_verification.png", dpi=120)
    print(" Spatial proximity matrix diagnostic plot saved as 'highway_distance_verification.png'.")

if __name__ == "__main__":
    build_ultimate_environment()