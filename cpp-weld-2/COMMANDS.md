# Quick Command Reference

## Build Commands

```bash
# Build with Makefile
make

# Clean and rebuild
make clean && make
```

## Run Commands - 4 Welding Scenarios

```bash
# Scenario 1: TIG with gas (η=0.75) - Best quality
./welding_sim --weld_process TIG --use_gas --save_video

# Scenario 2: TIG without gas (η=0.65) - Lower quality
./welding_sim --weld_process TIG --no-gas --save_video

# Scenario 3: Electrode with gas (η=0.85) - Unusual
./welding_sim --weld_process Electrode --use_gas --save_video

# Scenario 4: Electrode without gas (η=0.85) - Standard
./welding_sim --weld_process Electrode --no-gas --save_video
```

## Custom Physical Parameters

```bash
# Custom current and voltage
./welding_sim --weld_process TIG --use_gas --current 200 --voltage 30

# Custom welding speed
./welding_sim --weld_process TIG --use_gas --speed 0.008

# Custom material 1 properties (Mild Steel)
./welding_sim --weld_process TIG --use_gas --mat1_k 50.0 --mat1_cp 520.0 --mat1_rho 7900 --mat1_Tmelt 1850

# Custom material 2 properties (Stainless Steel)
./welding_sim --weld_process TIG --use_gas --mat2_k 18.0 --mat2_cp 510.0 --mat2_rho 8000 --mat2_Tmelt 1750

# All custom parameters combined
./welding_sim --weld_process TIG --use_gas --current 200 --voltage 30 --speed 0.008 --mat1_k 50.0
```

## Run All Scenarios

```bash
# Automatically run all 4 scenarios
./run_all_scenarios.sh
```

## Video Generation

```bash
# Generate video after simulation (if --save_video was used)
python3 generate_video.py --weld_process TIG --use_gas

# Custom video FPS
python3 generate_video.py --weld_process TIG --use_gas --fps 15

# Specify custom frames directory and output file
python3 generate_video.py --frames_dir output/video_frames --output my_video.mp4 --weld_process TIG --use_gas
```

## Optional: Snapshot at Specific Time

```bash
# Take snapshot at 5 seconds
./welding_sim --weld_process TIG --use_gas --snapshot_time 5.0
```

## Visualization Commands

```bash
# All 17 plots (recommended)
python3 visualize_complete.py

# Quick 6 plots
python3 visualize.py
```

## Clean Commands

```bash
# Clean build files
make clean

# Clean everything
make clean && rm -rf results/ output/
```

## Complete Workflows

### Quick Test with Video
```bash
make && \
./welding_sim --weld_process TIG --use_gas --save_video && \
python3 generate_video.py --weld_process TIG --use_gas && \
python3 visualize_complete.py
```

### Quick Test without Video
```bash
make && ./welding_sim --weld_process TIG --use_gas && python3 visualize_complete.py
```

### All Scenarios with Videos
```bash
make && ./run_all_scenarios.sh
```

## Help

```bash
./welding_sim --help
```
