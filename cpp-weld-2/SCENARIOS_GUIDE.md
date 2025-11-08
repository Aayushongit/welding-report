# Welding Scenarios Guide

This guide explains the 4 different welding scenarios supported by the simulation.

## Overview of Scenarios

The simulation supports **4 welding scenarios** based on two parameters:
1. **Welding Process**: TIG or Electrode
2. **Gas Shielding**: With or Without

This creates 2×2 = 4 scenarios with different efficiency values.

## Scenario Details

### Scenario 1: TIG with Gas (Recommended)
```bash
./welding_sim --weld_process TIG --use_gas
```

**Characteristics:**
- **Efficiency (η)**: 0.75
- **Heat Input**: Moderate
- **Application**: High-quality welds, controlled heat
- **Gas**: Argon or helium (typical)
- **Quality**: Excellent finish, minimal spatter

**When to use:**
- Precision welding
- Thin materials
- Stainless steel
- Aluminum
- Critical applications

---

### Scenario 2: TIG without Gas
```bash
./welding_sim --weld_process TIG --no-gas
```

**Characteristics:**
- **Efficiency (η)**: 0.65 (lower due to oxidation)
- **Heat Input**: Lower effective heat
- **Application**: Not recommended (oxidation issues)
- **Quality**: Poor due to contamination

**When to use:**
- Educational purposes only
- Understanding the importance of shielding gas
- Comparing with gas-shielded results

---

### Scenario 3: Electrode with Gas
```bash
./welding_sim --weld_process Electrode --use_gas
```

**Characteristics:**
- **Efficiency (η)**: 0.85
- **Heat Input**: High
- **Application**: Unusual (gas typically not used with electrode)
- **Quality**: Good but unconventional
- **Warning**: System will warn that this is atypical

**When to use:**
- Research purposes
- Special applications
- Comparative studies

---

### Scenario 4: Electrode without Gas (Standard)
```bash
./welding_sim --weld_process Electrode --no-gas
```

**Characteristics:**
- **Efficiency (η)**: 0.85
- **Heat Input**: High
- **Application**: Standard electrode welding
- **Gas**: Flux coating provides protection
- **Quality**: Good for thick materials

**When to use:**
- Heavy structural welding
- Thick steel plates
- Field welding
- Construction applications
- Cost-effective welding

---

## Running Individual Scenarios

### Quick Test - Single Scenario
```bash
# Build first
make

# Run specific scenario
./welding_sim --weld_process TIG --use_gas

# Visualize
python3 visualize_complete.py
```

### All Scenarios at Once
```bash
# Run all 4 scenarios automatically
./run_all_scenarios.sh
```

This will:
1. Build the executable (if needed)
2. Run all 4 scenarios
3. Save results in separate directories
4. Generate comparison summary

**Output Structure:**
```
results/
├── TIG_with_gas/
│   ├── simulation_results.csv
│   ├── thermal_history.csv
│   └── simulation_log.txt
├── TIG_without_gas/
│   ├── simulation_results.csv
│   ├── thermal_history.csv
│   └── simulation_log.txt
├── Electrode_with_gas/
│   ├── simulation_results.csv
│   ├── thermal_history.csv
│   └── simulation_log.txt
└── Electrode_without_gas/
    ├── simulation_results.csv
    ├── thermal_history.csv
    └── simulation_log.txt
```

---

## Efficiency Values Explained

| Scenario | η (Efficiency) | Q_total (W) | Reason |
|----------|---------------|-------------|---------|
| TIG + Gas | 0.75 | 2812.5 | Good arc stability, gas protection |
| TIG - Gas | 0.65 | 2437.5 | Heat loss to oxidation |
| Electrode + Gas | 0.85 | 3187.5 | High efficiency (unusual setup) |
| Electrode - Gas | 0.85 | 3187.5 | Flux provides protection |

**Base Parameters:**
- Voltage (V): 25V
- Current (I): 150A
- Q_total = η × V × I

---

## Expected Results Comparison

### Peak Temperatures
| Scenario | Approx. Peak T | Fusion Width | HAZ Size |
|----------|---------------|--------------|----------|
| TIG + Gas | ~2100 K | Medium | Moderate |
| TIG - Gas | ~1950 K | Smaller | Smaller |
| Electrode + Gas | ~2250 K | Larger | Larger |
| Electrode - Gas | ~2250 K | Larger | Larger |

### Weld Quality Indicators
| Scenario | Penetration | Width | Distortion | Quality |
|----------|------------|-------|------------|---------|
| TIG + Gas | Moderate | Narrow | Low | ⭐⭐⭐⭐⭐ |
| TIG - Gas | Low | Narrow | Low | ⭐⭐ |
| Electrode + Gas | High | Wide | High | ⭐⭐⭐⭐ |
| Electrode - Gas | High | Wide | High | ⭐⭐⭐⭐ |

---

## Visualizing Scenario Results

### After running all scenarios:

```bash
# Visualize TIG with gas
cd results/TIG_with_gas
python3 ../../visualize_complete.py
cd ../..

# Visualize Electrode without gas
cd results/Electrode_without_gas
python3 ../../visualize_complete.py
cd ../..
```

### Comparison Script
Create a custom comparison:

```python
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load all scenarios
scenarios = {
    'TIG+Gas': pd.read_csv('results/TIG_with_gas/simulation_results.csv'),
    'TIG-Gas': pd.read_csv('results/TIG_without_gas/simulation_results.csv'),
    'Electrode+Gas': pd.read_csv('results/Electrode_with_gas/simulation_results.csv'),
    'Electrode-Gas': pd.read_csv('results/Electrode_without_gas/simulation_results.csv')
}

# Compare peak temperatures along centerline
fig, ax = plt.subplots(figsize=(12, 6))

for name, df in scenarios.items():
    nx, ny = 151, 101
    T_max = df['T_max'].values.reshape(ny, nx)
    x = df['x'].values.reshape(ny, nx)[0, :] * 1000
    centerline = T_max[ny//2, :]
    ax.plot(x, centerline, linewidth=2, label=name)

ax.set_xlabel('Position (mm)', fontsize=12)
ax.set_ylabel('Peak Temperature (K)', fontsize=12)
ax.set_title('Centerline Temperature Comparison - All Scenarios', fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('scenario_comparison.png', dpi=300)
plt.show()
```

---

## Parameter Customization

You can take snapshots at specific times:

```bash
# Take snapshot at 5 seconds
./welding_sim --weld_process TIG --use_gas --snapshot_time 5.0
```

To change grid resolution or number of threads, edit the `SimulationConfig` structure in `WeldingSimulation.h`.

---

## Real-World Applications

### TIG Welding (with gas)
- **Industries**: Aerospace, automotive, food processing
- **Materials**: Stainless steel, aluminum, copper
- **Advantages**: Clean welds, precise control, no spatter
- **Disadvantages**: Slower, requires skill, more expensive

### Electrode Welding (without gas)
- **Industries**: Construction, shipbuilding, pipeline
- **Materials**: Carbon steel, thick sections
- **Advantages**: Fast, deep penetration, portable, cheap
- **Disadvantages**: More spatter, less precise, thicker welds

---

## Troubleshooting

### Issue: "Invalid weld_process"
```bash
Error: Invalid weld_process. Use 'TIG' or 'Electrode'.
```
**Solution:** Use exact spelling: `TIG` or `Electrode` (case-sensitive)

### Issue: Different results than expected
**Check:**
1. Grid resolution (--nx, --ny)
2. Time step (default: 0.02s)
3. Material properties
4. Boundary conditions

### Issue: Electrode + Gas warning
```
Warning: Gas is not typically used with electrode welding.
```
**This is normal** - the simulation will run, but this combination is unusual in practice.

---

## Performance Comparison

| Scenario | Relative Speed | Memory | Typical Use |
|----------|---------------|--------|-------------|
| All (same grid) | Same | Same | Same computational cost |

**Note:** All scenarios have the same computational cost for a given grid size. The only differences are in the physics (efficiency values).

---

## Best Practices

1. **Start with TIG + Gas** for validation
2. **Compare scenarios** to understand effects
3. **Use appropriate grid resolution**:
   - Quick: 151×101
   - Standard: 301×201
   - High-quality: 501×301
4. **Check thermal cycles** for cooling rate differences
5. **Examine fusion zones** for penetration comparison

---

## Quick Commands Summary

```bash
# Build
make

# Individual scenarios
./welding_sim --weld_process TIG --use_gas           # Scenario 1
./welding_sim --weld_process TIG --no-gas            # Scenario 2
./welding_sim --weld_process Electrode --use_gas     # Scenario 3
./welding_sim --weld_process Electrode --no-gas      # Scenario 4

# All scenarios
./run_all_scenarios.sh

# Visualize
python3 visualize_complete.py

# Help
./welding_sim --help
```

---

## References

- AWS D1.1: Structural Welding Code - Steel
- ISO 9606: Qualification testing of welders
- TIG Welding Handbook
- Electrode Welding Best Practices

---

**For more information, see:**
- README.md - General documentation
- QUICKSTART.md - Quick start guide
- VISUALIZATION_GUIDE.md - Plotting details
