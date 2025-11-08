cmake_minimum_required(VERSION 3.10)
project(WeldingSimulation VERSION 1.0)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find OpenMP
find_package(OpenMP REQUIRED)

if(OpenMP_CXX_FOUND)
    message(STATUS "OpenMP found: ${OpenMP_CXX_VERSION}")
else()
    message(FATAL_ERROR "OpenMP not found. Please install OpenMP support.")
endif()

# Compiler optimizations
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Set optimization flags
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -DNDEBUG")
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -Wall -Wextra")

# Source files
set(SOURCES
    WeldingSimulation.cpp
    main.cpp
)

# Header files
set(HEADERS
    WeldingSimulation.h
)

# Create executable
add_executable(welding_sim ${SOURCES} ${HEADERS})

# Link OpenMP
target_link_libraries(welding_sim PRIVATE OpenMP::OpenMP_CXX)

# Include directories
target_include_directories(welding_sim PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

# Print build information
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ compiler: ${CMAKE_CXX_COMPILER}")
message(STATUS "Compiler flags (Release): ${CMAKE_CXX_FLAGS_RELEASE}")

# Installation
install(TARGETS welding_sim DESTINATION bin)
