import streamlit as st
import mesa
import random
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches
import pandas as pd

st.set_page_config(page_title="Cary Urban Expansion Simulator", layout="wide")

# Custom UI Theme Consistency
st.markdown("""
    <style>
    .reportview-container { background-color: #0d1b15; }
    h1 { color: #2e7d32 !important; font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 800; letter-spacing: -0.5px; }
    .stMetric { background-color: #1b382b !important; padding: 15px !important; border-radius: 10px !important; border-left: 5px solid #d4af37 !important; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-family: monospace; }
    div[data-testid="stMetricLabel"] { color: #a1c7b3 !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 1. CORE LAND ENVIRONMENT CONTEXT
# ==========================================
class RealLandPatch(mesa.Agent):
    def __init__(self, model, x, y, classification_id, dist_to_highway, mxd_fenton_rad, mxd_chatham_rad):
        super().__init__(model)
        self.x = x
        self.y = y
        self.classification_id = classification_id
        self.dist_to_highway = dist_to_highway
        
        if classification_id == 0: 
            self.zone_type = "void"
            self.ldo_zoning = "OFF-MAP"
        elif classification_id == 5: 
            self.zone_type = "park"
            self.ldo_zoning = "R/R" 
        elif classification_id == 2: 
            self.zone_type = "established_housing"
            self.ldo_zoning = "R-12" 
        else: 
            self.zone_type = "developable"
            dist_to_fenton = np.sqrt((self.x - 40)**2 + (self.y - 35)**2)
            dist_to_chatham = np.sqrt((self.x - 22)**2 + (self.y - 22)**2)
            
            # PHASE 3 FEATURE: Zoning limits dynamically change based on sidebar input
            if dist_to_fenton < mxd_fenton_rad or dist_to_chatham < mxd_chatham_rad:
                self.ldo_zoning = "MXD" 
            else:
                self.ldo_zoning = "R-40" 

# ==========================================
# 2. DEVELOPER BEHAVIORAL LOGIC
# ==========================================
class BaseSpatialDeveloper(mesa.Agent):
    def __init__(self, model, agent_id):
        super().__init__(model)
        self.agent_id = agent_id
        self.development_id = 3 

    def calculate_score(self, step_coords, patch):
        return 0

    def get_infrastructural_gravity(self, coords):
        neighbors = self.model.grid.get_neighborhood(coords, moore=True, include_center=False)
        gravity_bonus = 0
        for n_coords in neighbors:
            for item in self.model.grid.get_cell_list_contents([n_coords]):
                if isinstance(item, RealLandPatch):
                    if item.zone_type in ["corp_development", "suburban_development", "established_housing"]:
                        gravity_bonus += 15  
        return gravity_bonus

    def develop_patch(self, cell_coords):
        for item in self.model.grid.get_cell_list_contents([cell_coords]):
            if isinstance(item, RealLandPatch) and item.zone_type == "developable":
                item.zone_type = self.agent_type_string
                item.classification_id = self.development_id

    def step(self):
        for item in self.model.grid.get_cell_list_contents([self.pos]):
            if isinstance(item, RealLandPatch) and item.zone_type == "developable":
                self.develop_patch(self.pos)

        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        best_score = -9999
        best_step = self.pos
        
        for step in possible_steps:
            for item in self.model.grid.get_cell_list_contents([step]):
                if isinstance(item, RealLandPatch) and item.zone_type == "developable" and item.ldo_zoning != "R/R":
                    score = self.calculate_score(step, item) + self.get_infrastructural_gravity(step)
                    if score > best_score:
                        best_score = score
                        best_step = step

        if best_step != self.pos:
            self.model.grid.move_agent(self, best_step)
            self.develop_patch(best_step)

class CorporateDeveloperAgent(BaseSpatialDeveloper):
    def __init__(self, model, agent_id):
        super().__init__(model, agent_id)
        self.agent_type_string = "corp_development"
        self.development_id = 4 

    def calculate_score(self, step_coords, patch):
        dist_to_bond = np.sqrt((patch.x - 15)**2 + (patch.y - 20)**2)
        
        # PHASE 3 FEATURE: Environmental buffer distance changes based on slider value
        if dist_to_bond <= self.model.park_buffer:
            return -9999 
        
        score = 150 - (patch.dist_to_highway * 3)
        if patch.ldo_zoning == "MXD":
            score += 60 
        elif patch.ldo_zoning == "R-40":
            score -= 40 
            
        return score

class SuburbanDeveloperAgent(BaseSpatialDeveloper):
    def __init__(self, model, agent_id):
        super().__init__(model, agent_id)
        self.agent_type_string = "suburban_development"
        self.development_id = 5 

    def calculate_score(self, step_coords, patch):
        dist_to_bond = np.sqrt((patch.x - 15)**2 + (patch.y - 20)**2)
        
        # PHASE 3 FEATURE: Environmental buffer distance changes based on slider value
        if dist_to_bond <= self.model.park_buffer or patch.ldo_zoning == "MXD":
            return -9999 
            
        if 8 <= patch.dist_to_highway <= 20:
            score = 90
        else:
            score = 30 - abs(patch.dist_to_highway - 14)
            
        if patch.ldo_zoning == "R-40":
            score += 40
        return score

# ==========================================
# 3. ENVIRONMENT SIMULATION CONTROLLER
# ==========================================
class CaryPredictiveModel(mesa.Model):
    def __init__(self, zone_path, highway_path, num_corp, num_suburban, fenton_rad, chatham_rad, park_buffer):
        super().__init__()
        self.zones = np.load(zone_path)
        self.highways = np.load(highway_path)
        self.height, self.width = self.zones.shape
        self.grid = mesa.space.MultiGrid(self.width, self.height, torus=False)
        self.developers = []
        self.park_buffer = park_buffer # Store buffer configuration

        mxd_compliant_pool = []
        r40_compliant_pool = []

        for y in range(self.height):
            for x in range(self.width):
                patch = RealLandPatch(self, x, y, self.zones[y][x], self.highways[y][x], fenton_rad, chatham_rad)
                self.grid.place_agent(patch, (x, y))
                if patch.zone_type == "developable":
                    if patch.ldo_zoning == "MXD":
                        mxd_compliant_pool.append((x, y))
                    elif patch.ldo_zoning == "R-40":
                        r40_compliant_pool.append((x, y))

        for i in range(num_corp):
            dev = CorporateDeveloperAgent(self, f"Corp_{i}")
            spawn_coords = random.choice(mxd_compliant_pool) if mxd_compliant_pool else random.choice(r40_compliant_pool)
            self.grid.place_agent(dev, spawn_coords)
            self.developers.append(dev)
            
        for i in range(num_suburban):
            dev = SuburbanDeveloperAgent(self, f"Sub_{i}")
            spawn_coords = random.choice(r40_compliant_pool) if r40_compliant_pool else random.choice(mxd_compliant_pool)
            self.grid.place_agent(dev, spawn_coords)
            self.developers.append(dev)

    def step(self):
        random.shuffle(self.developers)
        for developer in self.developers:
            developer.step()

def extract_map_matrix(model):
    matrix = np.zeros((model.height, model.width), dtype=int)
    for x in range(model.width):
        for y in range(model.height):
            for item in model.grid.get_cell_list_contents((x, y)):
                if isinstance(item, RealLandPatch):
                    if item.zone_type == "void": matrix[y][x] = 0
                    elif item.zone_type == "park": matrix[y][x] = 1
                    elif item.zone_type == "established_housing": matrix[y][x] = 2
                    elif item.zone_type == "developable": matrix[y][x] = 3
                    elif item.zone_type == "corp_development": matrix[y][x] = 4
                    elif item.zone_type == "suburban_development": matrix[y][x] = 5
                    break 
    return np.copy(matrix)

# ==========================================
# 4. FRONTEND VISUAL RENDERING
# ==========================================
st.title("Town of Cary Urban Expansion Forecasting Model")
st.markdown("🚧 *Interactive Geographic Growth & Canopy Inspector Engine*")

st.sidebar.header("🌲 Cary Simulation Panel")
corp_count = st.sidebar.slider("Corporate Developer Agents", min_value=1, max_value=20, value=10)
suburban_count = st.sidebar.slider("Suburban Developer Agents", min_value=1, max_value=20, value=10)

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Interactive 'What-If' LDO Policies")

# Dynamic Policy Toggles
park_buffer_val = st.sidebar.slider("🌳 Bond Park Buffer Radius", min_value=2, max_value=15, value=7, help="Adjust the environmental exclusion radius around public preserves.")
fenton_radius_val = st.sidebar.slider("🛍️ Fenton MXD Corridor Extent", min_value=5, max_value=25, value=15, help="Controls high-density development allowances near Fenton.")
chatham_radius_val = st.sidebar.slider("🏙️ Chatham St Commercial Core", min_value=5, max_value=20, value=12, help="Alters downtown density boundaries.")

st.sidebar.markdown("---")
run_button = st.sidebar.button("Execute Timeline Analysis", type="primary")

if 'sim_run' not in st.session_state:
    st.session_state.sim_run = False

if run_button or not st.session_state.sim_run:
    st.session_state.sim_run = True
    
    # Passing dynamic slider values directly to the simulation setup
    sim = CaryPredictiveModel(
        "real_cary_matrix.npy", "real_cary_highways.npy", 
        corp_count, suburban_count, 
        fenton_radius_val, chatham_radius_val, park_buffer_val
    )
    
    m_present = extract_map_matrix(sim)
    p_canopy = np.sum(m_present == 3)
    p_corp = np.sum(m_present == 4)
    p_sub = np.sum(m_present == 5)
    
    for _ in range(15): sim.step()
    m_10yr = extract_map_matrix(sim)
    m10_canopy = np.sum(m_10yr == 3)
    m10_corp = np.sum(m_10yr == 4)
    m10_sub = np.sum(m_10yr == 5)
    
    for _ in range(20): sim.step()
    m_20yr = extract_map_matrix(sim)
    m20_canopy = np.sum(m_20yr == 3)
    m20_corp = np.sum(m_20yr == 4)
    m20_sub = np.sum(m_20yr == 5)

    col1, col2, col3 = st.columns(3)
    col1.metric(label="🌳 Compliant Open Canopy Left", value=f"{m20_canopy} Pixels", delta=f"-{p_canopy - m20_canopy} since 2026", delta_color="inverse")
    col2.metric(label="🏢 Approved Corporate Zones", value=f"{m20_corp} Sites", delta=f"+{m20_corp - p_corp} built")
    col3.metric(label="🏡 Permitted Residential Clusters", value=f"{m20_sub} Sites", delta=f"+{m20_sub - p_sub} built")

    st.markdown("---")

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 7), dpi=300)
    fig.patch.set_facecolor('#ffffff')
    
    premium_palette = ListedColormap(['#ffffff', '#1b5e20', '#cfd8dc', '#e8f5e9', '#c62828', '#6a1b9a'])
    
    ax1.imshow(m_present, cmap=premium_palette, origin="lower", vmin=0, vmax=5, interpolation='none')
    ax1.set_title("1. Present Day Baseline (2026)", fontsize=14, fontweight='bold', color='#1b5e20')
    ax1.axis('off')
    
    ax2.imshow(m_10yr, cmap=premium_palette, origin="lower", vmin=0, vmax=5, interpolation='none')
    ax2.set_title("2. 10-Year LDO Forecast (2036)", fontsize=14, fontweight='bold', color='#1b5e20')
    ax2.axis('off')
    
    ax3.imshow(m_20yr, cmap=premium_palette, origin="lower", vmin=0, vmax=5, interpolation='none')
    ax3.set_title("3. 20-Year LDO Forecast (2046)", fontsize=14, fontweight='bold', color='#1b5e20')
    ax3.axis('off')
    
    legends = [
        mpatches.Patch(color='#1b5e20', label='LDO R/R Protected Zones (Parks/Water)'),
        mpatches.Patch(color='#cfd8dc', label='LDO R-12 Existing Infrastructure'),
        mpatches.Patch(color='#e8f5e9', label='Available Open Canopy Space'),
        mpatches.Patch(color='#c62828', label='LDO MXD Approved Districts (Fenton/Chatham Corporate)'),
        mpatches.Patch(color='#6a1b9a', label='LDO R-40 Single Family Subdivisions')
    ]
    
    fig.legend(handles=legends, loc='lower center', ncol=3, fontsize=10, frameon=True, facecolor='#f5f5f5', edgecolor='#d4af37')
    plt.subplots_adjust(bottom=0.2, top=0.9, wspace=0.1)
    
    st.pyplot(fig)

    # Analytics Section
    st.markdown("### 📊 Environmental Degradation & Structural Growth Analysis")
    
    chart_data = pd.DataFrame({
        'Timeline Year': ['2026 Baseline', '2036 (10-Yr Forecast)', '2046 (20-Yr Forecast)'],
        'Open Canopy Space': [p_canopy, m10_canopy, m20_canopy],
        'Corporate Infrastructure': [p_corp, m10_corp, m20_corp],
        'Suburban Subdivisions': [p_sub, m10_sub, m20_sub]
    }).set_index('Timeline Year')

    analytics_col1, analytics_col2 = st.columns([2, 1])

    with analytics_col1:
        st.markdown("**Land Conversion Trajectory Timeline**")
        st.line_chart(chart_data, color=["#2e7d32", "#c62828", "#6a1b9a"])

    with analytics_col2:
        st.markdown("**Metric Balance Ledger**")
        st.dataframe(chart_data, use_container_width=True)