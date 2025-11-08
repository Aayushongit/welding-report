# 🚀 START HERE - Welding Simulation

## Quick Start (30 seconds)

```bash
# 1. Build
make

# 2. Run with video generation
./welding_sim --weld_process TIG --use_gas --save_video

# 3. Generate video from frames
python3 generate_video.py --weld_process TIG --use_gas

# 4. Visualize all 17 plots
python3 visualize_complete.py
```

---

## 🎯 4 Welding Scenarios Available

```bash
# TIG with gas (η=0.75) - Best quality
./welding_sim --weld_process TIG --use_gas --save_video

# TIG without gas (η=0.65) - Lower quality
./welding_sim --weld_process TIG --no-gas --save_video

# Electrode with gas (η=0.85) - Unusual
./welding_sim --weld_process Electrode --use_gas --save_video

# Electrode without gas (η=0.85) - Standard
./welding_sim --weld_process Electrode --no-gas --save_video
```

---

## 🔥 Run All 4 Scenarios at Once

```bash
./run_all_scenarios.sh
```

Results will be in `results/` directory with subdirectories for each scenario.
Each scenario will have:
- simulation_results.csv (temperature data)
- thermal_history.csv (monitoring points)
- welding_simulation.mp4 (video animation)

---

## 📊 Visualization

```bash
# All 17 plots (recommended)
python3 visualize_complete.py

# Quick 6 plots
python3 visualize.py
```

---

## 📚 Documentation

- **START_HERE.md** (this file) - Quick start
- **COMMANDS.md** - All commands
- **SCENARIOS_GUIDE.md** - Detailed scenario explanations
- **README.md** - Full documentation

---

## ⚡ What You Get

- **4 Welding Scenarios** - TIG/Electrode with/without gas
- **17 Plots** - Complete visualization (matches Python version)
- **10x Faster** - OpenMP parallelized C++ code
- **All 4 Scenarios in 2 minutes** - Automated testing

---

## 🛠️ Options

```bash
# Custom parameters (current, voltage, speed)
./welding_sim --weld_process TIG --use_gas --current 200 --voltage 30 --speed 0.008

# Material properties customization
./welding_sim --weld_process TIG --use_gas --mat1_k 50.0 --mat1_Tmelt 1850

# Snapshot at specific time
./welding_sim --weld_process TIG --use_gas --snapshot_time 5.0

# Help (see all options)
./welding_sim --help
```

---

## ✅ That's It!

Just run:
```bash
make && ./run_all_scenarios.sh
```

And you'll have all 4 scenarios simulated with complete results!

---

**Questions? See SCENARIOS_GUIDE.md for detailed explanations.**
