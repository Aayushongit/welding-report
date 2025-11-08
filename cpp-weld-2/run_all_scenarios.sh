#!/bin/bash

# Script to run all 4 welding scenarios
# Scenarios:
#   1. TIG with gas (eta=0.75)
#   2. TIG without gas (eta=0.65)
#   3. Electrode with gas (eta=0.85, warning issued)
#   4. Electrode without gas (eta=0.85)

set -e  # Exit on error

echo "========================================================"
echo "  Welding Simulation - All Scenarios Test"
echo "========================================================"
echo ""

# Check if executable exists
if [ ! -f "welding_sim" ]; then
    echo "Executable not found. Building..."
    make clean
    make -j$(nproc)
    echo ""
fi

# Create results directory
mkdir -p results

# Array of scenarios (format: process:gas_status:args:gas_flag)
declare -a scenarios=(
    "TIG:with_gas:--weld_process TIG --use_gas --save_video:--use_gas"
    "TIG:without_gas:--weld_process TIG --no-gas --save_video:--no-gas"
    "Electrode:with_gas:--weld_process Electrode --use_gas --save_video:--use_gas"
    "Electrode:without_gas:--weld_process Electrode --no-gas --save_video:--no-gas"
)

# Run each scenario
for scenario in "${scenarios[@]}"; do
    IFS=':' read -r process gas_status args gas_flag <<< "$scenario"

    echo "========================================================"
    echo "Running Scenario: $process $gas_status"
    echo "========================================================"
    echo ""

    # Create output directory for this scenario
    output_dir="results/${process}_${gas_status}"
    mkdir -p "$output_dir"

    # Run simulation
    echo "Command: ./welding_sim $args"
    ./welding_sim $args | tee "${output_dir}/simulation_log.txt"

    # Generate video from frames
    if [ -d "output/video_frames" ] && [ "$(ls -A output/video_frames)" ]; then
        echo ""
        echo "Generating video for $process $gas_status..."
        python3 generate_video.py \
            --frames_dir output/video_frames \
            --output "${output_dir}/welding_simulation.mp4" \
            --fps 10 \
            --weld_process "$process" \
            $gas_flag
        echo "Video saved to: ${output_dir}/welding_simulation.mp4"
    fi

    # Move output files
    if [ -d "output" ]; then
        mv output/* "$output_dir/" 2>/dev/null || true
        rmdir output 2>/dev/null || true
    fi

    echo ""
    echo "Results saved to: $output_dir"
    echo ""
done

echo "========================================================"
echo "  All Scenarios Complete!"
echo "========================================================"
echo ""
echo "Results organized in results/ directory:"
echo "  - results/TIG_with_gas/"
echo "  - results/TIG_without_gas/"
echo "  - results/Electrode_with_gas/"
echo "  - results/Electrode_without_gas/"
echo ""
echo "To visualize each scenario:"
echo "  cd results/TIG_with_gas && python3 ../../visualize_complete.py"
echo ""
echo "Videos generated:"
echo "  - results/TIG_with_gas/welding_simulation.mp4"
echo "  - results/TIG_without_gas/welding_simulation.mp4"
echo "  - results/Electrode_with_gas/welding_simulation.mp4"
echo "  - results/Electrode_without_gas/welding_simulation.mp4"
echo ""

# Generate comparison summary
echo "========================================================"
echo "  Scenario Comparison Summary"
echo "========================================================"
echo ""

for scenario in "${scenarios[@]}"; do
    IFS=':' read -r process gas_status args <<< "$scenario"
    output_dir="results/${process}_${gas_status}"
    log_file="${output_dir}/simulation_log.txt"

    if [ -f "$log_file" ]; then
        echo "--- $process $gas_status ---"
        grep -E "(Simulating|Using|Warning|Power:|Peak|Fusion|HAZ)" "$log_file" | head -10
        echo ""
    fi
done

echo "========================================================"
echo "Done!"
echo "========================================================"
