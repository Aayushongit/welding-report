# High-Performance C++ Welding Simulation

Fast TIG welding simulation using Goldak's double ellipsoid model with OpenMP parallelization.

## Features

- **Goldak's Double Ellipsoid Heat Source Model** - Industry-standard for arc welding
- **OpenMP Parallel Computing** - Multi-threaded for maximum performance
- **Bi-material Simulation** - Mild Steel + Stainless Steel 304
- **Temperature-dependent Properties** - Realistic material behavior
- **Comprehensive Visualization** - 8 different plots and analysis

## Performance

- **10-100x faster** than pure Python implementation
- Utilizes all CPU cores with OpenMP
- Optimized with `-O3 -march=native -ffast-math`

## Quick Start

### 1. Compile and Run (Easy Mode)

```bash
cd cpp-weld
chmod +x build_and_run.sh
./build_and_run.sh
```

This will:
1. Compile the C++ code
2. Run the simulation
3. Generate all plots automatically

### 2. Manual Compilation

```bash
# Direct compilation
g++ -O3 -march=native -fopenmp -ffast-math sim-welding-new.cpp -o sim-welding-new

# Or using CMake
mkdir build && cd build
cmake ..
make
```

### 3. Run Simulation

```bash
# Run with all available CPU cores
./sim-welding-new

# Run with specific number of threads
./sim-welding-new 4
```

### 4. Visualize Results

```bash
python3 plot_weld_results.py
```

## Output Files

- `weld_results.csv` - Temperature data (x, y, T_max, T_final)
- `weld_config.txt` - Simulation configuration
- `output_cpp/` - Directory with 8 visualization plots

## Simulation Parameters

### Heat Source (Goldak Model)
- Voltage: 25 V
- Current: 150 A
- Efficiency: 0.85
- Welding speed: 6 mm/s
- Power: ~3.2 kW

### Grid
- Domain: 150 mm × 100 mm
- Resolution: 151 × 101 nodes
- Plate thickness: 6 mm

### Materials
- **Material 1 (Left):** Mild Steel
  - Melting point: 1811 K (1538°C)
  - Thermal conductivity: 45 W/m·K

- **Material 2 (Right):** Stainless Steel 304
  - Melting point: 1723 K (1450°C)
  - Thermal conductivity: 16.3 W/m·K

## Plots Generated

1. **Peak Temperature** - Contour plot with HAZ/fusion boundaries
2. **Fusion Zone & HAZ** - Highlighted zones with area calculations
3. **Centerline Profile** - Temperature along weld centerline
4. **Transverse Profile** - Temperature across weld width
5. **Temperature (°C)** - Results in Celsius
6. **3D Temperature** - 3D surface plot
7. **Weld Width** - Width variation along length
8. **Temperature Gradient** - Gradient magnitude

## Requirements

### C++ Compilation
- g++ with C++17 support
- OpenMP library (`libomp-dev` on Ubuntu)

Install on Ubuntu/Debian:
```bash
sudo apt-get install g++ libomp-dev
```

### Python Visualization
- numpy
- matplotlib

Install with pip:
```bash
pip install numpy matplotlib
```

## Customization

Edit `sim-welding-new.cpp` to modify:
- Grid resolution (lines 19-20)
- Material properties (lines 22-40)
- Heat source parameters (lines 38-49)
- Time step and solver settings (lines 54-56)

For faster demos, reduce grid size:
```cpp
int nx = 101;  // Instead of 151
int ny = 67;   // Instead of 101
```

## Comparison with Python Version

| Metric | Python (sim-weld.py) | C++ (sim-welding-new) |
|--------|---------------------|----------------------|
| Typical runtime | 10-30 minutes | 30-180 seconds |
| Grid size | 151 × 101 | 151 × 101 |
| Parallelization | Numba JIT | OpenMP (all cores) |
| Memory usage | Higher | Lower |
| Ease of use | Easy | Requires compilation |

## Troubleshooting

**Compilation error:**
```
fatal error: omp.h: No such file or directory
```
Solution: Install OpenMP library
```bash
sudo apt-get install libomp-dev
```

**Slow performance:**
- Check number of threads: The simulation prints "Using N OpenMP threads"
- Ensure `-O3` optimization is enabled during compilation
- Try reducing grid size for faster demos

## License

Educational/Research use
