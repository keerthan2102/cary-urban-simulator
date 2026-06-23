import mesa
import random
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

# 1. Environment Layer
class LandPatch(mesa.Agent):
    def __init__(self, model, x, y):
        super().__init__(model)
        self.x = x
        self.y = y
        self.has_trees = random.random() < 0.85  
        
        if self.x == 15 or self.x == 35:
            self.zone_type = "highway"  
            self.has_trees = False  
        elif 35 <= self.x <= 48 and 5 <= self.y <= 18:
            self.zone_type = "park"  
        else:
            self.zone_type = "normal"

# 2. BASE AI DEVELOPER (Handles shared movement mechanics)
class BaseDeveloper(mesa.Agent):
    def __init__(self, model, agent_id):
        super().__init__(model)
        self.agent_id = agent_id

    def calculate_score(self, step_coords):
        """Placeholder to be overridden by unique corporate strategies"""
        return 0

    def step(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        
        best_score = -999
        best_step = random.choice(possible_steps) 
        
        for step in possible_steps:
            cell_contents = self.model.grid.get_cell_list_contents([step])
            for item in cell_contents:
                if isinstance(item, LandPatch):
                    # Hard regulatory boundary: Parks are strictly illegal
                    if item.zone_type == "park":
                        continue 
                        
                    # Call the agent's unique polymorphic scoring logic
                    score = self.calculate_score(step)
                    
                    if score > best_score:
                        best_score = score
                        best_step = step

        self.model.grid.move_agent(self, best_step)

        # Inspect and Build
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        for item in cell_contents:
            if isinstance(item, LandPatch):
                if item.zone_type != "park" and item.has_trees:
                    item.has_trees = False  
                    self.model.total_houses_built += 1 

# 🏢 STRATEGY 1: Corporate High-Density Developer
class CorporateDeveloperAgent(BaseDeveloper):
    def calculate_score(self, step_coords):
        score = 0
        cell_contents = self.model.grid.get_cell_list_contents([step_coords])
        
        # Proximity to infrastructure bonus
        dist_h1 = abs(step_coords[0] - 15)
        dist_h2 = abs(step_coords[0] - 35)
        score += (15 - min(dist_h1, dist_h2))
        
        # CLUSTERING BONUS: Scan surroundings of this target step to look for existing houses
        neighbors = self.model.grid.get_neighborhood(step_coords, moore=True, include_center=False)
        for n_step in neighbors:
            n_contents = self.model.grid.get_cell_list_contents([n_step])
            for item in n_contents:
                if isinstance(item, LandPatch) and not item.has_trees and item.zone_type == "normal":
                    score += 3  # High-density incentive!
        return score

# 🏡 STRATEGY 2: Suburban Sprawl Developer
class SuburbanDeveloperAgent(BaseDeveloper):
    def calculate_score(self, step_coords):
        score = 0
        cell_contents = self.model.grid.get_cell_list_contents([step_coords])
        for item in cell_contents:
            if isinstance(item, LandPatch) and item.has_trees:
                score += 10  # Heavy preference for pristine forests
                
        # SPRAWL PENALTY: Check surroundings. If there are already houses, reduce attractiveness
        neighbors = self.model.grid.get_neighborhood(step_coords, moore=True, include_center=False)
        for n_step in neighbors:
            n_contents = self.model.grid.get_cell_list_contents([n_step])
            for item in n_contents:
                if isinstance(item, LandPatch) and not item.has_trees:
                    score -= 4  # Avoid congested urban centers!
        return score

# --- METRICS COLLECTORS ---
def count_forest(model):
    return sum(1 for agent in model.agents if isinstance(agent, LandPatch) and agent.has_trees)

def count_houses(model):
    return model.total_houses_built

# 3. Simulation Engine
class CarySimulation(mesa.Model):
    def __init__(self, width, height, num_corp, num_suburban):
        super().__init__()
        self.grid = mesa.space.MultiGrid(width, height, torus=False)
        self.total_houses_built = 0
        self.developers = []

        for x in range(width):
            for y in range(height):
                patch = LandPatch(self, x, y)
                self.grid.place_agent(patch, (x, y))

        # Spawn Corporate Developers
        for i in range(num_corp):
            dev = CorporateDeveloperAgent(self, agent_id=f"Corp_{i}")
            self.grid.place_agent(dev, (15, random.randint(10, 40)))
            self.developers.append(dev)

        # Spawn Suburban Developers
        for i in range(num_suburban):
            dev = SuburbanDeveloperAgent(self, agent_id=f"Sub_{i}")
            self.grid.place_agent(dev, (35, random.randint(10, 40)))
            self.developers.append(dev)

        self.datacollector = mesa.DataCollector(
            model_reporters={"Forest Patches": count_forest, "Houses Built": count_houses}
        )
        self.datacollector.collect(self)

    def step(self):
        random.shuffle(self.developers)
        for developer in self.developers:
            developer.step()
        self.datacollector.collect(self)

# 4. Visualization Dashboard Function
def draw_cary_dashboard(model):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    matrix = np.zeros((model.grid.height, model.grid.width))
    for x in range(model.grid.width):
        for y in range(model.grid.height):
            cell_contents = model.grid.get_cell_list_contents((x, y))
            for item in cell_contents:
                if isinstance(item, LandPatch):
                    if item.zone_type == "highway":
                        matrix[y][x] = 4  
                    elif item.zone_type == "park" and item.has_trees:
                        matrix[y][x] = 5  
                    elif item.has_trees:
                        matrix[y][x] = 1  
                    elif not item.has_trees and item.zone_type != "park":
                        matrix[y][x] = 2  
                        
    for dev in model.developers:
        dev_x, dev_y = dev.pos
        matrix[dev_y][dev_x] = 3  

    custom_colors = ListedColormap(['white', 'forestgreen', 'saddlebrown', 'red', 'black', 'skyblue'])
    ax1.imshow(matrix, cmap=custom_colors, origin="lower", vmin=0, vmax=5)
    ax1.set_title("Heterogeneous Agent Map Strategy")
    
    df = model.datacollector.get_model_vars_dataframe()
    ax2.plot(df["Houses Built"], label="Houses Built", color="saddlebrown", linewidth=2.5)
    ax2.plot(df["Forest Patches"], label="Remaining Forest", color="forestgreen", linewidth=2.5)
    ax2.set_xlabel("Simulation Turn (Time)")
    ax2.set_ylabel("Total Count")
    ax2.set_title("Environmental Footprint")
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    plt.savefig("cary_map.png")
    print(f"📊 Dashboard snapshot generated! Total houses built: {model.total_houses_built}")

# Run simulation with 3 Corporate Developers and 3 Suburban Developers for 75 turns
print("--- Initializing Multi-Strategy Competitive Cary Model ---")
sim = CarySimulation(width=50, height=50, num_corp=3, num_suburban=3)

for turn in range(1, 76):
    sim.step()

draw_cary_dashboard(sim)