import geopandas as gpd
import matplotlib.pyplot as plt

def fetch_real_cary_map():
    print("🛰️ Connecting to Town of Cary Open Data API Portal...")
    
    # Live REST API endpoint for Cary's Official Corporate Limits (GeoJSON format)
    url = "https://data.townofcary.org/api/v2/catalog/datasets/cary-corporate-limits/exports/geojson"
    
    try:
        # Stream the real-world boundary directly into a GeoDataFrame
        cary_gdf = gpd.read_file(url)
        print("✅ Successfully fetched Cary's Corporate Limits!")
        
        # Look at what the data table contains
        print("\n--- DATA OVERVIEW ---")
        print(cary_gdf.info())
        
        # 🗺️ EPSG:4326 uses degrees (Lat/Lon). We want a local projection system.
        # Let's project it to EPSG:2264 (NAD83 North Carolina State Plane feet)
        # This allows us to work with real units of measurement (feet/miles)
        cary_projected = cary_gdf.to_crs(epsg=2264)
        
        # Visual inspection: Plot Cary's actual geometry footprint
        fig, ax = plt.subplots(figsize=(10, 8))
        cary_projected.plot(ax=ax, color='lightgreen', edgecolor='darkgreen', alpha=0.7)
        
        ax.set_title("True Boundary Footprint: Town of Cary, NC", fontsize=14, fontweight='bold')
        ax.set_xlabel("State Plane X (Feet)")
        ax.set_ylabel("State Plane Y (Feet)")
        ax.grid(True, linestyle="--", alpha=0.5)
        
        plt.tight_layout()
        plt.savefig("real_cary_boundary.png")
        print("\n📸 Real-world Cary geographic footprint saved as 'real_cary_boundary.png'!")
        
        return cary_projected

    except Exception as e:
        print(f"❌ Failed to fetch data: {e}")
        return None

if __name__ == "__main__":
    cary_map = fetch_real_cary_map()