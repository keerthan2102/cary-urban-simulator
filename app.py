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

# 2. AI Developer
class DeveloperAgent(mesa.Agent):
    def __init__(self, model, agent_id):
        super().__init__(model)
        self.agent_id = agent_id

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
                    if item.zone_type == "park":
                        continue 
                    score = 0
                    if item.has_trees:
                        score += 5
                    dist_h1 = abs(step[0] - 15)
                    dist_h2 = abs(step[0] - 35)
                    min_dist = min(dist_h1, dist_h2)
                    score += (15 - min_dist) 
                    
                    if score > best_score:
                        best_score = score
                        best_step = step

        self.model.grid.move_agent(self, best_step)

        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        for item in cell_contents:
            if isinstance(item, LandPatch):
                if item.zone_type != "park" and item.has_trees:
                    item.has_trees = False  
                    self.model.total_houses_built += 1 

# --- FIXED HELPER FUNCTIONS FOR DATA COLLECTION ---
def count_forest(model):
    # Modern Mesa collects all agents in model.agents. 
    # We just filter for LandPatches that still have trees!
    return sum(1 for agent in model.agents if isinstance(agent, LandPatch) and agent.has_trees)

def count_houses(model):
    # Simply report the running tally from our model
    return model.total_houses_built

# 3. Simulation Engine
class CarySimulation(mesa.Model):
    def __init__(self, width, height, num_developers):
        super().__init__()
        self.grid = mesa.space.MultiGrid(width, height, torus=False)
        self.total_houses_built = 0
        self.developers = []

        for x in range(width):
            for y in range(height):
                patch = LandPatch(self, x, y)
                self.grid.place_agent(patch, (x, y))

        for i in range(num_developers):
            dev = DeveloperAgent(self, agent_id=i)
            spawn_x = 15 if i % 2 == 0 else 35
            spawn_y = random.randint(10, 40)
            self.grid.place_agent(dev, (spawn_x, spawn_y))
            self.developers.append(dev)

        # 🔑 NEW: Initialize the DataCollector to take metrics snapshots
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Forest Patches": count_forest,
                "Houses Built": count_houses
            }
        )
        # Record our starting baseline (Turn 0)
        self.datacollector.collect(self)

    def step(self):
        random.shuffle(self.developers)
        for developer in self.developers:
            developer.step()
        
        # 🔑 NEW: Record metrics at the end of every single turn
        self.datacollector.collect(self)

# --- NEW DASHBOARD VISUALIZATION FUNCTION ---
def draw_cary_dashboard(model):
    # Setup a side-by-side subplot canvas (1 row, 2 columns)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # --- PANEL 1: THE SPATIAL MAP ---
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
    ax1.set_title(f"Final Simulation Map")
    
    # --- PANEL 2: THE METRICS LINE GRAPH ---
    # Extract the tracking dataframe from our model's data collector
    df = model.datacollector.get_model_vars_dataframe()
    
    ax2.plot(df["Houses Built"], label="Houses Built", color="saddlebrown", linewidth=2.5)
    ax2.plot(df["Forest Patches"], label="Remaining Forest", color="forestgreen", linewidth=2.5)
    ax2.set_xlabel("Simulation Turn (Time)")
    ax2.set_ylabel("Total Count")
    ax2.set_title("Environmental Impact Over Time")
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    plt.savefig("cary_map.png")
    print(f"📊 Analytical Dashboard snapshot saved as 'cary_map.png'!")

# 4. Run the simulation for 60 turns
print("--- Initializing Analytical Dashboard Virtual Cary ---")
sim = CarySimulation(width=50, height=50, num_developers=5)

for turn in range(1, 61):
    sim.step()

draw_cary_dashboard(sim)