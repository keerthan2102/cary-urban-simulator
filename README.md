**Cary Urban Expansion Forecasting Model**

**An Agent-Based Simulation (ABS)** engine built with the Mesa framework to model, visualize, and inspect multi-temporal urban development patterns across the Town of Cary, North Carolina. This predictive model tracks spatial growth by simulating the divergent behaviors of corporate and suburban developer archetypes, utilizing real-world GIS baseline configurations.

**🚀 System Architecture Overview**
The application features a decoupled architecture where spatial geographic data layer states are isolated from active moving agents to ensure precise chronological snapshots.

**1. Spatial Patch Layer (RealLandPatch)**
Terrain Grid: Uses a MultiGrid environment mapping real Cary geographic boundaries.

Dynamic State Classification:

0: Void / Off-map territory (White)

1: Public Parks & Nature Reserves (Protected)

2: Existing Built Neighborhoods / Infrastructure (Static)

3: Available Open Spaces / Forest Canopy (Developable)

4: Corporate Cluster Developments (Crimson Red)

5: Suburban Sprawl Developments (Deep Purple)

**2. Behavioral Agent Archetypes**
The engine introduces two distinct structural paradigms to mimic real-world development incentives:

**🏢 Corporate Developer Agents (CorporateDeveloperAgent)**

OBJECTIVE: Prioritizes structural density and accessibility.

MATHEMATICAL WEIGHTING: High preference for immediate highway proximity combined with a strong clustering premium to build next to pre-existing built or corporate zones.

**🏡 Suburban Developer Agents (SuburbanDeveloperAgent)**

OBJECTIVE: Mimics standard decentralized residential sprawl.

MATHEMATICAL WEIGHTING: Seeks a geographic buffer zone sweet-spot (offset from intense highway noise but within commuting distance). Imposes a spatial crowding penalty to disperse out into open, untouched canopy spaces.

**📅 Multi-Temporal Forecasting Engine**
The timeline processor separates its execution steps into three distinct macro-observation horizons:

Present Day Cary Baseline (2026): A clean spatial render isolating the underlying terrain. Active simulation agents are completely filtered out to ensure a pristine 2026 baseline showing zero premature development.

10-Year Growth Forecast (2036): Runs an initial 15 simulation execution ticks to observe immediate corridor growth.

20-Year Growth Forecast (2046): Simulates an additional 20 ticks (35 total execution steps) to project final canopy depletion and fringe land saturation.

**🛠️ Repository File Structure**
Plaintext
├── app.py                         # Core simulation model, logic, and visualization dashboard
├── environment_builder.py         # Utility pipeline for preparing GIS matrices and infrastructure 
├── real_cary_matrix.npy           # Ground-truth Cary spatial classification matrix
└── real_cary_highways.npy         # Calculated matrix layer mapping grid distances to highway corridors

**🏃‍♂️ Quick Start Guide**
Prerequisites
Ensure you have Python installed alongside the required numerical mapping and simulation libraries:

Bash
pip install mesa numpy matplotlib
Running the Forecast Model
Execute the main application file from your project terminal window:

Bash
python app.py
Upon successful completion, the engine will process the timeline calculations, print status ticks to your console, and output a high-fidelity visual analysis chart saved directly to your workspace as cary_timeline_forecast.png.
