# Welding Simulation - C++ Implementation with OpenMP

High-performance welding heat transfer simulation using C++ and OpenMP for parallel computing. This implementation simulates TIG and Electrode welding processes with temperature-dependent material properties.

## Features

- **Parallel Computing**: OpenMP-accelerated computation for fast simulations
- **Goldak Heat Source Model**: Double ellipsoid heat distribution
- **Temperature-Dependent Properties**: Dynamic thermal conductivity, specific heat, and density
- **Multi-Material Support**: Simulates dissimilar metal welding (e.g., Mild Steel + Stainless Steel)
- **Welding Processes**: TIG and Electrode welding with gas shielding options
- **Data Export**: CSV output for temperature fields and thermal history

## Requirements

- C++17 compatible compiler (g++, clang++)
- CMake 3.10 or higher
- OpenMP support
- Linux/Unix environment (tested on Ubuntu/Debian)

## Compilation

### Step 1: Install Dependencies

On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install build-essential cmake libomp-dev
```

### Step 2: Build the Project

```bash
# Create build directory
mkdir build
cd build

# Configure with CMake
cmake ..

# Compile (use -j for parallel compilation)
make -j$(nproc)
```

The executable `welding_sim` will be created in the `build/` directory.

### Alternative: Direct Compilation

If you prefer not to use CMake:

```bash
g++ -std=c++17 -O3 -march=native -fopenmp \
    WeldingSimulation.cpp main.cpp \
    -o welding_sim
```

## Usage

### Basic Usage

```bash
./welding_sim
```

This runs the simulation with default parameters (TIG welding with shielding gas).

### Command Line Options

```bash
./welding_sim [options]

Options:
  --weld_process <TIG|Electrode>  Welding process (default: TIG)
  --use_gas                       Enable shielding gas (default: enabled)
  --no-gas                        Disable shielding gas
  --snapshot_time <seconds>       Time for snapshot (default: -1, disabled)
  --nx <value>                    Grid points in x direction (default: 151)
  --ny <value>                    Grid points in y direction (default: 101)
  --threads <value>               Number of OpenMP threads (default: auto)
  --help                          Show help message
```

### Examples

**TIG welding with gas:**
```bash
./welding_sim --weld_process TIG --use_gas
```

**Electrode welding without gas:**
```bash
./welding_sim --weld_process Electrode --no-gas
```

**Higher resolution simulation:**
```bash
./welding_sim --nx 301 --ny 201
```

**Control number of threads:**
```bash
./welding_sim --threads 8
```

**Take snapshot at specific time:**
```bash
./welding_sim --snapshot_time 5.0
```

## Output

Results are saved in the `output/` directory:

- **simulation_results.csv**: Complete temperature field data
  - Columns: `i, j, x, y, T_final, T_max`
  - Contains final and peak temperatures at each grid point

- **thermal_history.csv**: Temperature evolution at monitoring points
  - Columns: `time, T_pt1, T_pt2, T_pt3`
  - Three monitoring points: left (35%), center (50%), right (65%)

## Code Structure

```
.
├── WeldingSimulation.h      # Class definitions and configuration
├── WeldingSimulation.cpp    # Core simulation implementation
├── main.cpp                 # Entry point and CLI parsing
├── CMakeLists.txt          # Build configuration
└── README.md               # This file
```

### Key Components

1. **SimulationConfig**: Configuration structure for all simulation parameters
2. **Material**: Material properties with temperature-dependent behavior
3. **WeldingSimulation**: Main simulation class
   - Grid initialization
   - Goldak heat flux computation (OpenMP parallelized)
   - Material property computation (OpenMP parallelized)
   - Time-stepping solver (OpenMP parallelized)
   - Result export

## Performance Optimization

The implementation uses several optimization techniques:

1. **OpenMP Parallelization**:
   - Grid initialization: `#pragma omp parallel for collapse(2)`
   - Heat flux computation: Parallelized over all grid points
   - Material properties: Parallelized computation
   - Finite difference solver: Parallelized spatial loops

2. **Compiler Optimizations**:
   - `-O3`: Maximum optimization level
   - `-march=native`: CPU-specific optimizations
   - `-fopenmp`: OpenMP support

3. **Memory Access Patterns**:
   - Row-major order for cache-friendly access
   - Pre-allocated vectors to avoid reallocation

## Simulation Parameters

### Default Configuration

- **Domain**: 150mm × 100mm × 6mm
- **Grid**: 151 × 101 points
- **Materials**:
  - Material 1: Mild Steel (left half)
  - Material 2: Stainless Steel 304 (right half)
- **Heat Source**:
  - Voltage: 25V
  - Current: 150A
  - Welding speed: 6 mm/s
- **Time Step**: 0.02s

### Modifying Parameters

To change simulation parameters, edit the `SimulationConfig` structure in `WeldingSimulation.h` or modify `main.cpp` to accept additional command-line arguments.

## Comparison with Python Implementation

The C++ implementation provides significant performance improvements:

- **Speed**: 5-20x faster than Python (depending on grid size and number of cores)
- **Memory Efficiency**: More efficient memory usage
- **Scalability**: Better scaling with OpenMP threads
- **No Graph Generation**: Focuses on computation; use Python/MATLAB for visualization

## Visualization

Two Python scripts are provided for visualization:

### Option 1: Complete Visualization (All 17 Plots - Recommended)
```bash
python3 visualize_complete.py
```

This generates all 17 plots matching the original Python implementation:
- Plots 1-9: 2D temperature distributions, isotherms, gradients, zones
- Plots 10-13: 3D visualizations
- Plots 14-17: Thermal cycles, cooling rates, final temperature

### Option 2: Quick Visualization (6 Essential Plots)
```bash
python3 visualize.py
```

This generates the 6 most important plots for quick analysis.

### Custom Visualization

You can also create custom plots using the CSV files:

```python
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load results
df = pd.read_csv('output/simulation_results.csv')

# Reshape for plotting
nx, ny = 151, 101
T_max = df['T_max'].values.reshape(ny, nx)
x = df['x'].values.reshape(ny, nx)[0, :]
y = df['y'].values.reshape(ny, nx)[:, 0]

# Plot
plt.figure(figsize=(10, 6))
plt.contourf(x*1000, y*1000, T_max, levels=50, cmap='hot')
plt.colorbar(label='Temperature (K)')
plt.xlabel('x (mm)')
plt.ylabel('y (mm)')
plt.title('Peak Temperature Distribution')
plt.show()
```

## Troubleshooting

### OpenMP not found
- Install OpenMP: `sudo apt-get install libomp-dev`
- For clang: `sudo apt-get install libomp-5-dev`

### Compilation errors
- Ensure C++17 support: Check compiler version (`g++ --version`)
- Update CMake: `sudo apt-get install cmake`

### Slow performance
- Check thread count: `echo $OMP_NUM_THREADS`
- Set explicitly: `export OMP_NUM_THREADS=8` or use `--threads` option
- Use Release build: Ensure CMake is configured with `-DCMAKE_BUILD_TYPE=Release`

## License

This is an educational/research code for welding simulation.

## Contact

For questions or issues, refer to the project documentation or course materials.
