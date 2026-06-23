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
        self.has_trees = random.random() < 0.85  # Slightly higher forest density
        
        # Scale infrastructure rules to fit a 50x50 map
        if self.x == 15 or self.x == 35:
            self.zone_type = "highway"  # TWO vertical highways now!
            self.has_trees = False  
        elif 35 <= self.x <= 48 and 5 <= self.y <= 18:
            self.zone_type = "park"  # A massive nature preserve
        else:
            self.zone_type = "normal"

# 2. AI Developer
class DeveloperAgent(mesa.Agent):
    def __init__(self, model, agent_id):
        super().__init__(model)
        self.agent_id = agent_id
        self.built_count = 0  

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
                        
                    # Calculate proximity to BOTH highways and favor the closest one
                    dist_h1 = abs(step[0] - 15)
                    dist_h2 = abs(step[0] - 35)
                    min_dist = min(dist_h1, dist_h2)
                    score += (15 - min_dist) # Bonus for staying near highways
                    
                    if score > best_score:
                        best_score = score
                        best_step = step

        self.model.grid.move_agent(self, best_step)

        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        for item in cell_contents:
            if isinstance(item, LandPatch):
                if item.zone_type != "park" and item.has_trees:
                    item.has_trees = False  
                    self.built_count += 1
                    self.model.total_houses_built += 1 # Track city-wide growth

# 3. Upgraded Simulation Engine
class CarySimulation(mesa.Model):
    def __init__(self, width, height, num_developers):
        super().__init__()
        self.grid = mesa.space.MultiGrid(width, height, torus=False)
        self.total_houses_built = 0
        self.developers = []

        # Generate the 50x50 map
        for x in range(width):
            for y in range(height):
                patch = LandPatch(self, x, y)
                self.grid.place_agent(patch, (x, y))

        # Spawn MULTIPLE developers at different points along the highways
        for i in range(num_developers):
            dev = DeveloperAgent(self, agent_id=i)
            spawn_x = 15 if i % 2 == 0 else 35
            spawn_y = random.randint(10, 40)
            self.grid.place_agent(dev, (spawn_x, spawn_y))
            self.developers.append(dev)

    def step(self):
        # Activate all developers in random order each turn to keep it fair
        random.shuffle(self.developers)
        for developer in self.developers:
            developer.step()

# --- SCALE VISUALIZATION FUNCTION ---
def draw_cary_map(model):
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
                        
    # Draw all active developers on the map
    for dev in model.developers:
        dev_x, dev_y = dev.pos
        matrix[dev_y][dev_x] = 3  

    custom_colors = ListedColormap(['white', 'forestgreen', 'saddlebrown', 'red', 'black', 'skyblue'])

    plt.figure(figsize=(8, 8)) # Increased image size to see detail
    plt.imshow(matrix, cmap=custom_colors, origin="lower", vmin=0, vmax=5)
    plt.title(f"Macro Cary Simulation - Total Houses Built: {model.total_houses_built}")
    
    plt.savefig("cary_map.png")
    print(f"Macro map snapshot saved! Total built city-wide: {model.total_houses_built}")

# 4. Run the macro simulation for 50 turns
print("--- Initializing Macro-Scale Virtual Cary ---")
sim = CarySimulation(width=50, height=50, num_developers=5)

for turn in range(1, 51):
    sim.step()

draw_cary_map(sim)