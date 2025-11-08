# Visualization Guide

This document describes the visualization options available for the welding simulation results.

## Available Visualization Scripts

### 1. `visualize_complete.py` - Complete Visualization (Recommended)

**Generates all 17 plots matching the original Python implementation**

```bash
python3 visualize_complete.py
```

#### 2D Temperature Plots (Plots 1-9)

1. **Detailed Temperature Isotherms**
   - Filled contour plot with temperature distribution
   - Multiple labeled isotherm lines (400K to 2200K)
   - Color-coded: Blue (cool), Orange (HAZ), Red (fusion)
   - Shows material interface line

2. **Isotherm-Only View**
   - Clean view showing only isotherm contour lines
   - White background for clarity
   - Prominent HAZ and fusion boundary lines
   - No filled contours

3. **Color-Coded Isotherm Families**
   - Gray background with temperature zones
   - Three families: Cool (blue), HAZ (orange), Fusion (red)
   - Shows temperature gradient patterns

4. **Temperature Gradient Magnitude**
   - Shows |∇T| (magnitude of temperature gradient)
   - Plasma colormap for gradient visualization
   - Highlights regions of rapid temperature change
   - Useful for understanding heat flow patterns

5. **Fusion Zone & HAZ Regions**
   - Filled regions showing fusion zone (red) and HAZ (orange)
   - Black boundary lines at critical temperatures
   - Clear zone delineation

6. **Centerline Temperature**
   - 1D plot along weld centerline (y = 0)
   - Shows both peak and final temperatures
   - Reference lines for all isotherm levels
   - Melting point and HAZ boundary marked

7. **Transverse Temperature Profile**
   - Cross-section perpendicular to weld at center
   - Shows temperature variation across weld width
   - Reference temperature lines

8. **Weld Width Along Length**
   - Fusion zone width as function of position
   - Shows average weld width
   - Useful for quality assessment

9. **Temperature (°C) with Isotherms**
   - Same as Plot 1 but in Celsius instead of Kelvin
   - For easier interpretation

#### 3D Visualizations (Plots 10-13)

10. **3D Peak Temperature Surface**
    - 3D surface plot of peak temperature
    - Hot colormap
    - Rotatable view (25° elevation, 45° azimuth)

11. **3D with Isotherm Projections**
    - 3D surface with isotherms projected on base
    - Jet colormap
    - Shows temperature levels clearly

12. **3D Zones Scatter**
    - Scatter plot showing fusion zone (red squares) and HAZ (orange dots)
    - Emphasizes affected regions
    - Sparse sampling for performance

13. **3D Temperature Gradient**
    - 3D surface of gradient magnitude
    - Plasma colormap
    - Shows heat flow in 3D

#### Thermal History Plots (Plots 14-17)

14. **Thermal Cycles**
    - Temperature vs time at three monitoring points
    - Point 1 (blue): Left (35% along weld)
    - Point 2 (red): Center (50% along weld)
    - Point 3 (green): Right (65% along weld)
    - Shows heating and cooling behavior

15. **Cooling Rates**
    - dT/dt vs time for each monitoring point
    - Negative values indicate cooling
    - Important for microstructure prediction

16. **Final Temperature**
    - 2D temperature distribution at end of simulation
    - Monitoring points marked
    - Shows residual heat distribution

17. **Peak T vs Position**
    - Centerline peak temperature with filled zones
    - Red fill: Fusion zone
    - Orange fill: HAZ
    - Clear visualization of weld extent

### 2. `visualize.py` - Quick Visualization

**Generates 6 essential plots for rapid analysis**

```bash
python3 visualize.py
```

#### Generated Plots:

1. **Peak Temperature** - Filled contour with isotherms
2. **Final Temperature** - Final state temperature distribution
3. **Centerline Temperature** - 1D profile along weld
4. **Thermal Cycles** - Temperature vs time at monitor points
5. **3D Temperature** - 3D surface plot
6. **Zones** - Fusion and HAZ regions

**Use this for:**
- Quick validation during development
- Fast turnaround when testing parameters
- Initial assessment of results

## Output Files

### CSV Data Files
- `output/simulation_results.csv` - Complete temperature field data
- `output/thermal_history.csv` - Time series at monitoring points

### Generated Plots

All plots are saved as high-resolution PNG files (300 DPI) in the `output/` directory.

**Complete visualization:**
```
output/
├── 1_detailed_isotherms.png
├── 2_isotherm_only.png
├── 3_color_coded_isotherms.png
├── 4_temperature_gradient.png
├── 5_fusion_haz_zones.png
├── 6_centerline_temperature.png
├── 7_transverse_temperature.png
├── 8_weld_width.png
├── 9_temperature_celsius.png
├── 10_3d_peak_temperature.png
├── 11_3d_isotherm_projections.png
├── 12_3d_zones_scatter.png
├── 13_3d_temperature_gradient.png
├── 14_thermal_cycles.png
├── 15_cooling_rates.png
├── 16_final_temperature.png
└── 17_peak_temperature_vs_position.png
```

## Which Script to Use?

### Use `visualize_complete.py` when:
- ✅ Final analysis and documentation
- ✅ Need all details for research/reports
- ✅ Comparing with Python implementation
- ✅ Quality assessment and validation
- ✅ Understanding complex thermal behavior

### Use `visualize.py` when:
- ✅ Quick parameter testing
- ✅ Rapid feedback during development
- ✅ Basic validation
- ✅ Time-constrained analysis
- ✅ Preliminary results

## Usage Examples

### Basic Usage
```bash
# Run simulation
./welding_sim

# Generate all plots
python3 visualize_complete.py
```

### With Build Script
```bash
# Build, run, and visualize automatically
./build_and_run.sh
```

### Custom Analysis
```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('output/simulation_results.csv')

# Extract specific region
region = df[(df['x'] > 0.05) & (df['x'] < 0.10)]

# Custom plot
plt.scatter(region['x'], region['y'], c=region['T_max'], cmap='hot')
plt.colorbar()
plt.show()
```

## Dependencies

### Required Python Packages
```bash
pip install numpy matplotlib pandas
```

Or using the system package manager:
```bash
sudo apt-get install python3-numpy python3-matplotlib python3-pandas
```

## Troubleshooting

### Issue: "File not found"
**Solution:** Run the simulation first to generate CSV files
```bash
./welding_sim
```

### Issue: "Module not found"
**Solution:** Install required packages
```bash
pip install numpy matplotlib pandas
```

### Issue: 3D plots not showing
**Solution:** Ensure matplotlib has 3D support (should be default)

### Issue: Memory error with large grids
**Solution:** Use `visualize.py` instead, or reduce grid resolution

## Performance

### Timing Estimates

| Script | Grid 151×101 | Grid 301×201 |
|--------|-------------|--------------|
| `visualize.py` | ~5 seconds | ~15 seconds |
| `visualize_complete.py` | ~30 seconds | ~90 seconds |

### Memory Usage

- Small grids (151×101): ~200 MB
- Large grids (301×201): ~800 MB

## Customization

Both scripts can be easily modified to:
- Add new plots
- Change colormaps
- Adjust figure sizes
- Modify labels and titles
- Add custom annotations

See the source code for examples.

## Comparison with Python Implementation

The `visualize_complete.py` script generates **exactly the same 17 plots** as the original `pyfile.py`, ensuring:
- ✅ Identical visualization
- ✅ Same color schemes
- ✅ Same isotherm levels
- ✅ Same layout and formatting
- ✅ Direct comparison possible

## Tips for Best Results

1. **Always run simulation first** before visualization
2. **Use complete visualization** for final results
3. **Check both peak and final temperatures** for full picture
4. **Examine thermal cycles** to understand heating/cooling rates
5. **Look at zones** to assess weld quality
6. **Compare centerline and transverse** profiles for symmetry

## Further Analysis

For advanced analysis, load the CSV files directly:

```python
import pandas as pd
import numpy as np

# Load results
df = pd.read_csv('output/simulation_results.csv')
history = pd.read_csv('output/thermal_history.csv')

# Calculate statistics
print(f"Peak temperature: {df['T_max'].max():.1f} K")
print(f"Average peak temp: {df['T_max'].mean():.1f} K")

# Find fusion zone area
nx, ny = 151, 101
T_max = df['T_max'].values.reshape(ny, nx)
fusion = T_max >= 1767.0
fusion_area = fusion.sum() * (dx * dy) * 1e6  # mm²
print(f"Fusion area: {fusion_area:.2f} mm²")
```

---

**For questions or issues with visualization, refer to README.md or the source code comments.**
