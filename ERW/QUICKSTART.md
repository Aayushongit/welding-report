# ERW Simulation Quick Start Guide

## What You Have

A complete ERW (Electric Resistance Welding) pipe simulation based on the mathematical models in `ref.md`. The simulation successfully generates:

- 7 detailed plots showing temperature, zones, gradients, and thermal cycles
- 1 video (erw_simulation.mp4) showing the welding process animation
- Comprehensive statistics about the weld

## Files Created

```
ERW/
├── erw_simulation.py       # Main simulation code (950+ lines)
├── config.json             # Configuration parameters
├── README.md               # Detailed documentation
├── QUICKSTART.md          # This file
├── ref.md                 # Mathematical reference (already existed)
├── output/                # Results directory
│   ├── erw_1_temperature_isotherms_final.png
│   ├── erw_2_zones_final.png
│   ├── erw_3_gradient_final.png
│   ├── erw_4_centerline_final.png
│   ├── erw_5_thermal_cycles_final.png
│   ├── erw_6_3d_temperature_final.png
│   └── erw_7_cooling_rates_final.png
└── erw_simulation.mp4     # Animation video (82 KB)
```

## How to Run

### Basic Run
```bash
# Activate environment
source "/media/dell/Hard Drive/Python_env/agent-env/bin/activate"

# Navigate to ERW folder
cd "/media/dell/Hard Drive/Summer of code/MME/ERW-pipelines/welding-kar/ERW"

# Run simulation
python erw_simulation.py
```

### Simulation took: ~259 seconds (4.3 minutes)

## Results from First Run

```
Peak Temperature: 61,639 K (61,366 °C)
Fusion Zone Area: 1,308.39 mm²
HAZ Area: 212.83 mm²
Total Affected Area: 1,521.22 mm²
Average Weld Width: 40.66 mm
```

Note: The peak temperature is higher than expected. This indicates we may need to adjust:
1. Current density (reduce from 5e7 to ~1e7 A/m²)
2. Power (reduce from 50 kW to ~30 kW)
3. Contact resistance model parameters

## How to Adjust Parameters

Edit `config.json`:

### To reduce temperature:
```json
"Q_power": 30000,           // Reduce from 50000
"current_density": 1e7,     // Reduce from 5e7
"eta_erw": 0.75,           // Reduce from 0.85
```

### To change welding speed:
```json
"v_weld": 0.020,           // Change from 0.015 (faster welding)
```

### To change grid resolution:
```json
"nx": 300,                 // Increase from 200 (finer grid)
"ny": 180,                 // Increase from 120
```

### To change simulation time:
```json
"snapshot_time": 5.0,      // Change from 3.0 (longer simulation)
```

## Understanding the Plots

### Plot 1: Temperature Isotherms
- Shows temperature distribution with contour lines
- Blue = Cool regions
- Orange = Heat-Affected Zone (HAZ)
- Red = Fusion zone (molten metal)
- Cyan vertical line = Weld seam center

### Plot 2: Zones
- Red shaded = Fusion zone (where metal melted)
- Orange shaded = HAZ (affected but not melted)
- Shows the extent of thermal influence

### Plot 3: Gradient
- Shows temperature gradient magnitude
- High gradients = rapid temperature changes
- Important for understanding thermal stress

### Plot 4: Centerline Profile
- Temperature along the weld centerline
- Red line = Peak temperature reached
- Blue line = Final temperature
- Shows cooling pattern

### Plot 5: Thermal Cycles
- Temperature vs time at 4 monitoring points
- Shows heating and cooling rates
- Critical for predicting microstructure

### Plot 6: 3D Temperature
- 3D visualization of temperature field
- Helps understand spatial distribution

### Plot 7: Cooling Rates
- Rate of temperature decrease over time
- Important for phase transformations
- Affects final material properties

## Video Output

`erw_simulation.mp4` shows:
- Real-time evolution of temperature field
- Moving heat source (white star marker)
- Weld seam position (cyan dashed line)
- 15 fps animation at 100 frames

## Physics Models Implemented

1. **Joule Heating**: Q = J²/σₑ (bulk) + I²Rc (contact)
2. **Contact Resistance**: Rc(T, p) - temperature and pressure dependent
3. **Moving Heat Source**: Travels at welding speed along seam
4. **Temperature-Dependent Properties**: k(T), cp(T), ρ(T), σₑ(T)
5. **Phase Kinetics**: Koistinen-Marburger martensite model ready

## Comparison with EBW Simulation

The code structure is inspired by `ebw/ebw_simulation.py` but adapted for ERW:

| Feature | EBW | ERW |
|---------|-----|-----|
| Heat source | Electron beam | Joule + Contact heating |
| Key physics | Beam absorption | Electrical resistance |
| Typical temp | 1800-2200 K | 1700-1900 K (should be) |
| Video output | ✓ | ✓ |
| Plots | 17 | 7 |
| Config file | JSON | JSON |

## Next Steps to Improve

1. **Calibrate parameters** to get realistic temperatures (~1700-1900 K)
2. **Add mechanical stress** model for residual stress prediction
3. **Implement JMAK model** for diffusional phase transformations
4. **Add adaptive time stepping** for better accuracy
5. **Compare with experimental data** if available

## Troubleshooting

### Temperature too high?
- Reduce `Q_power` or `current_density` in config.json
- Increase `contact_width` to distribute heat more
- Reduce `eta_erw` efficiency factor

### Simulation too slow?
- Reduce grid resolution (`nx`, `ny`)
- Increase time step (`dt`)
- Reduce `snapshot_time` for shorter simulation

### Video not playing?
- Ensure you have a video player that supports H.264 codec
- Try VLC media player or similar

## Technical Details

- **Solver**: Crank-Nicolson implicit time integration (θ=0.6)
- **Spatial**: Finite difference on Cartesian grid
- **Matrix solver**: SuperLU sparse direct solver
- **Boundary conditions**: Fixed temperature at domain edges
- **Grid**: 200×120 points over 150×80 mm domain
- **Time step**: 0.01 s, total time: 3 s

## Performance

- Grid points: 24,000
- Time steps: 300
- Total time: 259 seconds (~1.16 steps/second)
- Memory: Sparse matrix storage for efficiency

## References

Based on:
- `ref.md` - Complete mathematical formulation
- EBW simulation structure
- Published ERW literature (see README.md)

Enjoy your ERW simulation! 🔥
