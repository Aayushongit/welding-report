# 🎉 New Features - Video Generation & Configurable Parameters

## 📹 Video Generation

The simulation now supports generating **MP4 video animations** showing the temperature field evolution during welding.

### How to Use:

1. **Run simulation with video frame saving:**
   ```bash
   ./welding_sim --weld_process TIG --use_gas --save_video
   ```

2. **Generate video from saved frames:**
   ```bash
   python3 generate_video.py --weld_process TIG --use_gas
   ```

3. **Video output:**
   - Saved as `output/welding_simulation.mp4`
   - Shows real-time temperature field evolution
   - Labeled with process type and time
   - Default: 10 FPS

### Video Options:

```bash
# Custom FPS
python3 generate_video.py --fps 15 --weld_process TIG --use_gas

# Custom output location
python3 generate_video.py --output my_video.mp4 --weld_process TIG --use_gas

# Process different frame directory
python3 generate_video.py --frames_dir results/TIG_with_gas/video_frames \
                          --output results/TIG_with_gas/video.mp4 \
                          --weld_process TIG --use_gas
```

### Requirements:

Install video generation dependencies:
```bash
# Activate virtual environment
source "/media/dell/Hard Drive/Python_env/agent-env/bin/activate"

# Install packages
pip install imageio imageio-ffmpeg

# On Ubuntu, ensure ffmpeg is installed
sudo apt-get install ffmpeg
```

---

## ⚙️ Configurable Physical Parameters

All major welding parameters are now configurable via command-line arguments!

### Welding Parameters:

```bash
# Current (Amperes)
./welding_sim --weld_process TIG --use_gas --current 200

# Voltage (Volts)
./welding_sim --weld_process TIG --use_gas --voltage 30

# Welding speed (m/s)
./welding_sim --weld_process TIG --use_gas --speed 0.008
```

### Material 1 Properties (Mild Steel):

```bash
# Thermal conductivity (W/m·K)
./welding_sim --mat1_k 50.0

# Specific heat (J/kg·K)
./welding_sim --mat1_cp 520.0

# Density (kg/m³)
./welding_sim --mat1_rho 7900

# Melting temperature (K)
./welding_sim --mat1_Tmelt 1850
```

### Material 2 Properties (Stainless Steel 304):

```bash
# Thermal conductivity (W/m·K)
./welding_sim --mat2_k 18.0

# Specific heat (J/kg·K)
./welding_sim --mat2_cp 510.0

# Density (kg/m³)
./welding_sim --mat2_rho 8000

# Melting temperature (K)
./welding_sim --mat2_Tmelt 1750
```

### Combined Example:

```bash
./welding_sim --weld_process TIG --use_gas \
              --current 200 --voltage 30 --speed 0.008 \
              --mat1_k 50.0 --mat1_cp 520.0 \
              --mat2_k 18.0 --mat2_Tmelt 1750 \
              --save_video
```

---

## 📊 Mathematical Modeling

The simulation uses accurate physical models:

### Heat Input:
```
Q_total = η × V × I
```
Where:
- η = welding efficiency (0.65-0.85 depending on process/gas)
- V = voltage (Volts)
- I = current (Amperes)

### Heat Transfer:
```
ρ·cp·∂T/∂t = ∇·(k·∇T) + Q
```
Temperature-dependent properties:
- k(T): Thermal conductivity increases with temperature
- cp(T): Specific heat increases near melting point
- ρ(T): Density decreases with temperature

### Goldak Heat Source:
Double-ellipsoid model for arc welding heat distribution

---

## 🎬 Automated Video Generation for All Scenarios

The `run_all_scenarios.sh` script now automatically generates videos for all 4 scenarios:

```bash
./run_all_scenarios.sh
```

Output structure:
```
results/
├── TIG_with_gas/
│   ├── simulation_results.csv
│   ├── thermal_history.csv
│   ├── welding_simulation.mp4    ← NEW!
│   └── simulation_log.txt
├── TIG_without_gas/
│   └── welding_simulation.mp4    ← NEW!
├── Electrode_with_gas/
│   └── welding_simulation.mp4    ← NEW!
└── Electrode_without_gas/
    └── welding_simulation.mp4    ← NEW!
```

---

## 📝 Default Values

| Parameter | Default | Unit | Description |
|-----------|---------|------|-------------|
| **Welding Parameters** |
| Current (I) | 150 | A | Welding current |
| Voltage (V) | 25 | V | Arc voltage |
| Speed (v) | 0.006 | m/s | Travel speed |
| **Material 1 (Mild Steel)** |
| k₁ | 45.0 | W/m·K | Thermal conductivity |
| cp₁ | 500.0 | J/kg·K | Specific heat |
| ρ₁ | 7850 | kg/m³ | Density |
| T_melt₁ | 1811 | K | Melting temperature |
| **Material 2 (SS304)** |
| k₂ | 16.3 | W/m·K | Thermal conductivity |
| cp₂ | 500.0 | J/kg·K | Specific heat |
| ρ₂ | 7900 | kg/m³ | Density |
| T_melt₂ | 1723 | K | Melting temperature |
| **Video Options** |
| FPS | 10 | frames/s | Video frame rate |

---

## 🔬 Example Use Cases

### Research: Study Effect of Current

```bash
# Low current (100A)
./welding_sim --weld_process TIG --use_gas --current 100 --save_video
python3 generate_video.py --output low_current.mp4 --weld_process TIG --use_gas

# Medium current (150A, default)
./welding_sim --weld_process TIG --use_gas --current 150 --save_video
python3 generate_video.py --output med_current.mp4 --weld_process TIG --use_gas

# High current (200A)
./welding_sim --weld_process TIG --use_gas --current 200 --save_video
python3 generate_video.py --output high_current.mp4 --weld_process TIG --use_gas
```

### Education: Compare Materials

```bash
# Aluminum-like properties
./welding_sim --weld_process TIG --use_gas \
              --mat1_k 200.0 --mat1_Tmelt 933 \
              --save_video

# Copper-like properties
./welding_sim --weld_process TIG --use_gas \
              --mat1_k 400.0 --mat1_Tmelt 1358 \
              --save_video
```

### Industry: Optimize Process

```bash
# Fast welding (high speed)
./welding_sim --weld_process TIG --use_gas --speed 0.010 --save_video

# High penetration (high current, low speed)
./welding_sim --weld_process TIG --use_gas --current 200 --speed 0.004 --save_video
```

---

## 🎯 Quick Reference

### With Video:
```bash
./welding_sim --weld_process TIG --use_gas --save_video
python3 generate_video.py --weld_process TIG --use_gas
```

### Custom Parameters:
```bash
./welding_sim --weld_process TIG --use_gas \
              --current 200 --voltage 30 --speed 0.008
```

### See All Options:
```bash
./welding_sim --help
```

---

## 📚 Documentation Files

- **START_HERE.md** - Quick start with new features
- **COMMANDS.md** - All command examples
- **NEW_FEATURES.md** - This file
- **README.md** - Complete documentation

---

## 🆕 What Changed?

### Code Changes:
1. **WeldingSimulation.h** - Added video frame config and method
2. **WeldingSimulation.cpp** - Implemented frame export during simulation
3. **main.cpp** - Added 15+ new command-line arguments
4. **generate_video.py** - New Python script for video generation
5. **run_all_scenarios.sh** - Integrated video generation

### New Files:
- `generate_video.py` - Video generation script

### Updated Files:
- `START_HERE.md` - Added video examples
- `COMMANDS.md` - Added parameter examples
- `run_all_scenarios.sh` - Auto-generate videos

---

## ✅ Benefits

1. **Visual Understanding** - See temperature evolution over time
2. **Parameter Control** - Test different welding conditions easily
3. **Material Studies** - Compare different materials
4. **Process Optimization** - Find optimal parameters
5. **Education** - Better teaching tool with animations
6. **Documentation** - Videos for reports and presentations

---

**Happy Welding! 🔥**
