#!/bin/bash

# Bash script to run all 4 TIG/Electrode welding scenarios
# Scenarios:
# 1. TIG with gas
# 2. TIG without gas
# 3. Electrode with gas
# 4. Electrode without gas

echo "========================================="
echo "Running All Welding Simulation Scenarios"
echo "========================================="
echo ""

# Activate Python virtual environment
source "/media/dell/Hard Drive/Python_env/agent-env/bin/activate"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Scenario 1: TIG with gas
echo "========================================="
echo "Scenario 1: TIG with Gas"
echo "========================================="
python sim-weld.py --weld_process TIG --use_gas --output_dir output_tig_gas --snapshot_time 12.0
if [ $? -eq 0 ]; then
    echo "✓ TIG with gas simulation completed successfully!"
else
    echo "✗ TIG with gas simulation failed!"
fi
echo ""

# Scenario 2: TIG without gas
echo "========================================="
echo "Scenario 2: TIG without Gas"
echo "========================================="
python sim-weld.py --weld_process TIG --no-gas --output_dir output_tig_no_gas --snapshot_time 12.0
if [ $? -eq 0 ]; then
    echo "✓ TIG without gas simulation completed successfully!"
else
    echo "✗ TIG without gas simulation failed!"
fi
echo ""

# Scenario 3: Electrode with gas
echo "========================================="
echo "Scenario 3: Electrode with Gas"
echo "========================================="
python sim-weld.py --weld_process Electrode --use_gas --output_dir output_electrode_gas --snapshot_time 12.0
if [ $? -eq 0 ]; then
    echo "✓ Electrode with gas simulation completed successfully!"
else
    echo "✗ Electrode with gas simulation failed!"
fi
echo ""

# Scenario 4: Electrode without gas
echo "========================================="
echo "Scenario 4: Electrode without Gas"
echo "========================================="
python sim-weld.py --weld_process Electrode --no-gas --output_dir output_electrode_no_gas --snapshot_time 12.0
if [ $? -eq 0 ]; then
    echo "✓ Electrode without gas simulation completed successfully!"
else
    echo "✗ Electrode without gas simulation failed!"
fi
echo ""

echo "========================================="
echo "All Scenarios Completed!"
echo "========================================="
echo ""
echo "Results saved in:"
echo "  - output_tig_gas/"
echo "  - output_tig_no_gas/"
echo "  - output_electrode_gas/"
echo "  - output_electrode_no_gas/"
echo ""
