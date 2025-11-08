cmake_minimum_required(VERSION 3.10)
project(WeldingSimulation)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find OpenMP
find_package(OpenMP REQUIRED)

# Compiler optimizations
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -march=native -ffast-math")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")

# Add executable
add_executable(welding-sim main.cpp)

# Link OpenMP
target_link_libraries(welding-sim OpenMP::OpenMP_CXX)

# Print build information
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "CXX flags: ${CMAKE_CXX_FLAGS}")
message(STATUS "OpenMP found: ${OpenMP_CXX_FOUND}")
message(STATUS "OpenMP version: ${OpenMP_CXX_VERSION}")
