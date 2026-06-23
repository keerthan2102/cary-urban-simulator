import geopandas as gpd
import matplotlib.pyplot as plt

def layer_cary_data():
    print("🛰️ Connecting to Town of Cary Open Data Portal API...")
    
    # 1. Fetch Corporate Limits
    boundary_url = "https://data.townofcary.org/api/v2/catalog/datasets/cary-corporate-limits/exports/geojson"
    try:
        cary_gdf = gpd.read_file(boundary_url).to_crs(epsg=2264)
        print("✅ Corporate limits loaded.")
    except Exception as e:
        print(f"❌ Failed to load boundary: {e}")
        return None, None

    # 2. Fetch Parks Polygons (Updated official dataset identifier!)
    parks_url = "https://data.townofcary.org/api/v2/catalog/datasets/parks-and-recreation-feature-polygons/exports/geojson"
    print("🌲 Connecting to updated Parks & Recreation feature server...")
    
    try:
        parks_gdf = gpd.read_file(parks_url).to_crs(epsg=2264)
        print(f"✅ Successfully loaded {len(parks_gdf)} public park/greenway polygon entities!")
        
        # Print dataset columns to inspect what attributes we can use
        print("\n--- PARKS DATASET SCHEMA COLUMNS ---")
        print(parks_gdf.columns.tolist())
        print("------------------------------------\n")
        
        # Clip the parks data so it matches the corporate limits perfectly
        print("✂️ Clipping spatial geometries to corporate limits...")
        cary_parks = gpd.clip(parks_gdf, cary_gdf)
        
        # Visualizing our true multi-layer base map
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Layer 1: Corporate Border Base
        cary_gdf.plot(ax=ax, color='#f2f2f2', edgecolor='#9c9c9c', linewidth=1.5, label="Cary Boundary")
        
        # Layer 2: True Park Polygons
        cary_parks.plot(ax=ax, color='forestgreen', alpha=0.8, edgecolor='darkgreen', label="Protected Public Parks")
        
        ax.set_title("Cary Simulation Map: Real Boundaries & Protected Parks", fontsize=14, fontweight='bold')
        ax.set_xlabel("State Plane X (Feet)")
        ax.set_ylabel("State Plane Y (Feet)")
        ax.grid(True, linestyle="--", alpha=0.3)
        
        plt.tight_layout()
        plt.savefig("real_cary_with_parks.png")
        print("📸 Real multi-layer base map saved as 'real_cary_with_parks.png'!")
        
        return cary_gdf, cary_parks

    except Exception as e:
        print(f"❌ Failed to fetch or overlay data: {e}")
        return None, None

if __name__ == "__main__":
    boundary, parks = layer_cary_data()