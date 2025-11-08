#!/bin/bash

# Build and run script for welding simulation
# This script provides an easy way to compile and run the simulation

set -e  # Exit on error

echo "=== Welding Simulation Build and Run Script ==="
echo ""

# Check for required tools
if ! command -v g++ &> /dev/null; then
    echo "Error: g++ not found. Please install g++:"
    echo "  sudo apt-get install build-essential"
    exit 1
fi

# Function to build with CMake
build_cmake() {
    echo "Building with CMake..."
    if ! command -v cmake &> /dev/null; then
        echo "Error: cmake not found. Please install cmake:"
        echo "  sudo apt-get install cmake"
        exit 1
    fi

    mkdir -p build
    cd build
    cmake ..
    make -j$(nproc)
    cd ..
    echo "Build complete: build/welding_sim"
}

# Function to build with Makefile
build_make() {
    echo "Building with Makefile..."
    make clean
    make -j$(nproc)
    echo "Build complete: welding_sim"
}

# Function to build directly
build_direct() {
    echo "Building directly with g++..."
    g++ -std=c++17 -O3 -march=native -fopenmp \
        WeldingSimulation.cpp main.cpp \
        -o welding_sim
    echo "Build complete: welding_sim"
}

# Parse command line arguments
BUILD_METHOD="cmake"
RUN_SIM=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --cmake)
            BUILD_METHOD="cmake"
            shift
            ;;
        --make)
            BUILD_METHOD="make"
            shift
            ;;
        --direct)
            BUILD_METHOD="direct"
            shift
            ;;
        --build-only)
            RUN_SIM=false
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --cmake       Use CMake to build (default)"
            echo "  --make        Use Makefile to build"
            echo "  --direct      Build directly with g++"
            echo "  --build-only  Only build, don't run simulation"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build
case $BUILD_METHOD in
    cmake)
        build_cmake
        EXECUTABLE="build/welding_sim"
        ;;
    make)
        build_make
        EXECUTABLE="welding_sim"
        ;;
    direct)
        build_direct
        EXECUTABLE="welding_sim"
        ;;
esac

# Run simulation if requested
if [ "$RUN_SIM" = true ]; then
    echo ""
    echo "=== Running Simulation ==="
    echo ""
    ./$EXECUTABLE "$@"

    # Check if visualization script exists
    if [ -f "visualize_complete.py" ]; then
        echo ""
        echo "=== Generating All 17 Plots ==="
        echo ""
        python3 visualize_complete.py
    elif [ -f "visualize.py" ]; then
        echo ""
        echo "=== Generating Quick Plots ==="
        echo ""
        python3 visualize.py
    fi
else
    echo ""
    echo "Build complete. To run the simulation:"
    echo "  ./$EXECUTABLE"
fi
