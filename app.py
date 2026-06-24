import mesa
import random
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches

# 1. High-Fidelity Spatial Patch Layer
class RealLandPatch(mesa.Agent):
    def __init__(self, model, x, y, classification_id, dist_to_highway):
        super().__init__(model)
        self.x = x
        self.y = y
        self.classification_id = classification_id
        self.dist_to_highway = dist_to_highway
        
        if classification_id == 0: 
            self.zone_type = "void"               
        elif classification_id == 5: 
            self.zone_type = "park"               
        elif classification_id == 2: 
            self.zone_type = "established_housing"
        else: 
            self.zone_type = "developable"         

# 2. Base Developer Brain with Spatial Heuristics
class BaseSpatialDeveloper(mesa.Agent):
    def __init__(self, model, agent_id):
        super().__init__(model)
        self.agent_id = agent_id
        self.development_id = 3 # Overwritten by subclasses

    def calculate_score(self, step_coords, patch):
        return 0

    def step(self):
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        best_score = -9999
        best_step = self.pos
        
        for step in possible_steps:
            for item in self.model.grid.get_cell_list_contents([step]):
                if isinstance(item, RealLandPatch) and item.zone_type == "developable":
                    score = self.calculate_score(step, item)
                    if score > best_score:
                        best_score = score
                        best_step = step
                        
        if best_step != self.pos:
            self.model.grid.move_agent(self, best_step)
            for item in self.model.grid.get_cell_list_contents([best_step]):
                if isinstance(item, RealLandPatch) and item.zone_type == "developable":
                    # Mark specific developer archetype state tracking IDs
                    item.zone_type = self.agent_type_string
                    item.classification_id = self.development_id 
                    self.model.total_houses_built += 1

# 🏢 Archetype 1: Corporate Cluster Strategy (Aggressive proximity to Highways & Existing Density)
class CorporateDeveloperAgent(BaseSpatialDeveloper):
    def __init__(self, model, agent_id):
        super().__init__(model, agent_id)
        self.agent_type_string = "corp_development"
        self.development_id = 4 # Maps to Crimson Red

    def calculate_score(self, step_coords, patch):
        # Heavy preference for immediate highway proximity (low distance = high score)
        score = 150 - (patch.dist_to_highway * 5)
        
        neighbors = self.model.grid.get_neighborhood(step_coords, moore=True, include_center=False)
        for n_step in neighbors:
            for item in self.model.grid.get_cell_list_contents([n_step]):
                # Likes clustering near established infrastructure or corporate hubs
                if isinstance(item, RealLandPatch) and item.classification_id in [2, 4]:
                    score += 15 
        return score

# 🏡 Archetype 2: Suburban Sprawl Strategy (Seeks buffer zones away from noise, values open land)
class SuburbanDeveloperAgent(BaseSpatialDeveloper):
    def __init__(self, model, agent_id):
        super().__init__(model, agent_id)
        self.agent_type_string = "suburban_development"
        self.development_id = 5 # Maps to Deep Purple

    def calculate_score(self, step_coords, patch):
        # Suburban sweet-spot: Accessible to highway commute but offset from edge noise
        if 8 <= patch.dist_to_highway <= 20:
            score = 90
        else:
            score = 30 - abs(patch.dist_to_highway - 14)
            
        neighbors = self.model.grid.get_neighborhood(step_coords, moore=True, include_center=False)
        for n_step in neighbors:
            for item in self.model.grid.get_cell_list_contents([n_step]):
                # Avoids packing into tight clusters (congestion penalty)
                if isinstance(item, RealLandPatch) and item.classification_id in [2, 4, 5]:
                    score -= 8 
        return score

# 3. Simulation Model
class CaryPredictiveModel(mesa.Model):
    def __init__(self, zone_path, highway_path, num_corp, num_suburban):
        super().__init__()
        self.zones = np.load(zone_path)
        self.highways = np.load(highway_path)
        self.height, self.width = self.zones.shape
        self.grid = mesa.space.MultiGrid(self.width, self.height, torus=False)
        self.total_houses_built = 0
        self.developers = []

        valid_spawn = []
        for y in range(self.height):
            for x in range(self.width):
                patch = RealLandPatch(self, x, y, self.zones[y][x], self.highways[y][x])
                self.grid.place_agent(patch, (x, y))
                if patch.zone_type == "developable":
                    valid_spawn.append((x, y))

        for i in range(num_corp):
            dev = CorporateDeveloperAgent(self, f"Corp_{i}")
            self.grid.place_agent(dev, random.choice(valid_spawn))
            self.developers.append(dev)
            
        for i in range(num_suburban):
            dev = SuburbanDeveloperAgent(self, f"Sub_{i}")
            self.grid.place_agent(dev, random.choice(valid_spawn))
            self.developers.append(dev)

    def step(self):
        random.shuffle(self.developers)
        for developer in self.developers:
            developer.step()

# 🗃️ Robust Agent-Filtered Map State Extractor
def extract_map_matrix(model):
    matrix = np.zeros((model.height, model.width), dtype=int)
    for x in range(model.width):
        for y in range(model.height):
            for item in model.grid.get_cell_list_contents((x, y)):
                if isinstance(item, RealLandPatch):
                    if item.zone_type == "void": 
                        matrix[y][x] = 0
                    elif item.zone_type == "park": 
                        matrix[y][x] = 1
                    elif item.zone_type == "established_housing": 
                        matrix[y][x] = 2
                    elif item.zone_type == "developable": 
                        matrix[y][x] = 3
                    elif item.zone_type == "corp_development": 
                        matrix[y][x] = 4
                    elif item.zone_type == "suburban_development": 
                        matrix[y][x] = 5
                    break 
    return np.copy(matrix)

# 4. Timeline Generation Execution
if __name__ == "__main__":
    print("🎬 Running Comparative Archetype Growth Engine...")
    sim = CaryPredictiveModel("real_cary_matrix.npy", "real_cary_highways.npy", 15, 15)
    
    m_present = extract_map_matrix(sim)
    
    print("⏳ Simulating 10 Years of Behavioral Growth (2036)...")
    for _ in range(15): 
        sim.step()
    m_10yr = extract_map_matrix(sim)
    
    print("⏳ Simulating 20 Years of Behavioral Growth (2046)...")
    for _ in range(20): 
        sim.step()
    m_20yr = extract_map_matrix(sim)
    
    # 🎨 Multi-Archetype Visual Mapping Layout
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(24, 8))
    
    # Value Indices: 0=Void(White), 1=Parks(Meadow), 2=Existing(Beige), 3=Open Land(Sage), 4=Corp(Crimson Red), 5=Suburban(Deep Purple)
    premium_palette = ListedColormap(['#ffffff', '#a1dbb2', '#e5dfd3', '#dbebd1', '#c0392b', '#8e44ad'])
    
    ax1.imshow(m_present, cmap=premium_palette, origin="lower", vmin=0, vmax=5)
    ax1.set_title("1. Present Day Cary Baseline (2026)", fontsize=14, fontweight='bold', color='#2c3e50', pad=10)
    ax1.axis('off')
    
    ax2.imshow(m_10yr, cmap=premium_palette, origin="lower", vmin=0, vmax=5)
    ax2.set_title("2. 10-Year Growth Forecast (2036)", fontsize=14, fontweight='bold', color='#2c3e50', pad=10)
    ax2.axis('off')
    
    ax3.imshow(m_20yr, cmap=premium_palette, origin="lower", vmin=0, vmax=5)
    ax3.set_title("3. 20-Year Growth Forecast (2046)", fontsize=14, fontweight='bold', color='#2c3e50', pad=10)
    ax3.axis('off')
    
    # Detailed Explanatory Legend for Policy Inspection
    legends = [
        mpatches.Patch(color='#a1dbb2', label='Public Parks & Nature Reserves'),
        mpatches.Patch(color='#e5dfd3', label='Existing Built Neighborhoods'),
        mpatches.Patch(color='#dbebd1', label='Available Open Spaces (Forest/Canopy)'),
        mpatches.Patch(color='#c0392b', label='Corporate Clusters (Transit & Density Driven)'),
        mpatches.Patch(color='#8e44ad', label='Suburban Sprawl (Noise Offset & Space Driven)')
    ]
    fig.legend(handles=legends, loc='lower center', ncol=5, fontsize=11, frameon=True, shadow=True, bbox_to_anchor=(0.5, 0.04))
    
    plt.suptitle("Town of Cary Urban Expansion Forecasting Model — Archetype Inspection", fontsize=20, fontweight='bold', y=0.95, color='#2c3e50')
    plt.tight_layout(rect=[0, 0.08, 1, 0.92])
    
    plt.savefig("cary_timeline_forecast.png", dpi=200)
    print("📸 High-fidelity segmented timeline analysis dashboard saved as 'cary_timeline_forecast.png'!")