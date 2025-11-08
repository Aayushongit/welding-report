# Quick Start Guide

## Fastest Way to Run

### Option 1: Using the Build Script (Recommended)

```bash
# Make script executable (first time only)
chmod +x build_and_run.sh

# Build and run with default settings
./build_and_run.sh

# Or use Makefile instead of CMake
./build_and_run.sh --make
```

### Option 2: Using Makefile

```bash
# Build
make

# Run
./welding_sim

# Or do both in one command
make run
```

### Option 3: Using CMake

```bash
# Build
mkdir build && cd build
cmake ..
make -j$(nproc)

# Run
./welding_sim
```

### Option 4: Direct Compilation

```bash
g++ -std=c++17 -O3 -march=native -fopenmp \
    WeldingSimulation.cpp main.cpp -o welding_sim

./welding_sim
```

## Visualization

After running the simulation, visualize results:

### All 17 plots (matching Python version):
```bash
python3 visualize_complete.py
```

### Quick 6-plot summary:
```bash
python3 visualize.py
```

Plots will be created in `output/` directory.

## Common Use Cases

### Run All 4 Welding Scenarios

```bash
./run_all_scenarios.sh
```

This runs:
1. TIG with gas (η=0.75)
2. TIG without gas (η=0.65)
3. Electrode with gas (η=0.85)
4. Electrode without gas (η=0.85)

### Individual Scenarios

```bash
# TIG with gas (best quality)
./welding_sim --weld_process TIG --use_gas

# TIG without gas (lower quality)
./welding_sim --weld_process TIG --no-gas

# Electrode with gas (unusual)
./welding_sim --weld_process Electrode --use_gas

# Electrode without gas (standard)
./welding_sim --weld_process Electrode --no-gas
```

### Take Snapshot at 5 seconds

```bash
./welding_sim --weld_process TIG --use_gas --snapshot_time 5.0
```

## Output Files

Results are saved in the `output/` directory:

- `simulation_results.csv` - Complete temperature field
- `thermal_history.csv` - Temperature at monitoring points

## Troubleshooting

**OpenMP not found:**
```bash
sudo apt-get install libomp-dev
```

**Python visualization issues:**
```bash
pip install numpy matplotlib pandas
```

**Permission denied:**
```bash
chmod +x build_and_run.sh visualize.py
```

## File Structure

```
cpp-weld-2/
├── WeldingSimulation.h       # Header file
├── WeldingSimulation.cpp     # Implementation
├── main.cpp                  # Main program
├── CMakeLists.txt           # CMake configuration
├── Makefile                 # Makefile (alternative)
├── build_and_run.sh         # Build script
├── visualize.py             # Visualization script
├── README.md                # Full documentation
└── QUICKSTART.md           # This file
```

## Performance Tips

1. **Use more threads:** `--threads 16`
2. **Release build:** Already enabled in CMakeLists.txt
3. **Larger grids:** Increase `--nx` and `--ny`
4. **Check CPU usage:** `htop` while running

## Next Steps

1. Run with default settings to verify installation
2. Experiment with different welding processes
3. Adjust grid resolution for your needs
4. Modify parameters in `WeldingSimulation.h` for custom materials
5. Use `visualize.py` to analyze results

For detailed documentation, see [README.md](README.md)
