#!/bin/bash
# Complete TIG welding simulation pipeline with video generation

echo "=============================================="
echo "  TIG Welding Simulation Pipeline"
echo "=============================================="

# Create output directory
mkdir -p output_cpp

# Step 1: Compile
echo ""
echo "Step 1: Compiling C++ simulation..."
# Use CMake for compilation
echo "Building with CMake..."
mkdir -p build
cd build
cmake ..
make

if [ $? -ne 0 ]; then
    echo "✗ CMake build failed!"
    echo "Make sure you have g++ with OpenMP support and CMake installed:"
    echo "  sudo apt-get install g++ libomp-dev cmake"
    exit 1
fi
cd ..
echo "✓ CMake build successful!"

# Step 2: Run simulation
echo ""
echo "Step 2: Running TIG welding simulation..."
echo "=============================================="
./build/welding-sim

if [ $? -ne 0 ]; then
    echo "✗ Simulation failed!"
    exit 1
fi

# Step 3: Generate plots
echo ""
echo "=============================================="
echo "Step 3: Generating analysis plots..."
python3 plot_weld_results.py

if [ $? -ne 0 ]; then
    echo "✗ Plot generation failed!"
    exit 1
fi

# Step 4: Create video
echo ""
echo "=============================================="
echo "Step 4: Creating video with temperature contours..."
python3 create_video.py

if [ $? -ne 0 ]; then
    echo "✗ Video creation failed!"
    echo "Make sure ffmpeg is installed:"
    echo "  sudo apt-get install ffmpeg"
    exit 1
fi

# Summary
echo ""
echo "=============================================="
echo "✓ TIG Welding Simulation Complete!"
echo "=============================================="
echo ""
echo "Output files created in output_cpp/:"
echo "  📊 weld_results.csv - Temperature data"
echo "  📊 weld_config.txt - Simulation parameters"
echo ""
echo "Plots (7 images):"
echo "  📈 1_peak_temperature.png"
echo "  📈 2_fusion_haz.png"
echo "  📈 3_centerline_profile.png"
echo "  📈 4_transverse_profile.png"
echo "  📈 5_temperature_celsius.png"
echo "  📈 6_3d_temperature.png"
echo "  📈 7_weld_width.png"
echo "  📈 8_temperature_gradient.png"
echo ""
echo "Video:"
echo "  🎬 tig_welding_simulation.mp4 - Animated temperature contours"
echo "  🖼️  frame_initial.png - Initial state"
echo "  🖼️  frame_final.png - Final state"
echo ""
echo "=============================================="
