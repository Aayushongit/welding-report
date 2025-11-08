# Makefile for Welding Simulation
# Alternative to CMake for quick compilation

CXX = g++
CXXFLAGS = -std=c++17 -O3 -march=native -Wall -Wextra -fopenmp
LDFLAGS = -fopenmp

TARGET = welding_sim
SOURCES = WeldingSimulation.cpp main.cpp
HEADERS = WeldingSimulation.h
OBJECTS = $(SOURCES:.cpp=.o)

# Default target
all: $(TARGET)

# Link object files to create executable
$(TARGET): $(OBJECTS)
	@echo "Linking $(TARGET)..."
	$(CXX) $(OBJECTS) $(LDFLAGS) -o $(TARGET)
	@echo "Build complete: $(TARGET)"

# Compile source files to object files
%.o: %.cpp $(HEADERS)
	@echo "Compiling $<..."
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Clean build files
clean:
	@echo "Cleaning build files..."
	rm -f $(OBJECTS) $(TARGET)
	@echo "Clean complete"

# Clean output files
clean-output:
	@echo "Cleaning output files..."
	rm -rf output/
	@echo "Output cleaned"

# Clean everything
distclean: clean clean-output

# Run with default parameters
run: $(TARGET)
	./$(TARGET)

# Run with custom grid resolution
run-hires: $(TARGET)
	./$(TARGET) --nx 301 --ny 201

# Show help
help:
	@echo "Welding Simulation Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  make              - Build the executable"
	@echo "  make clean        - Remove build files"
	@echo "  make clean-output - Remove output files"
	@echo "  make distclean    - Remove all generated files"
	@echo "  make run          - Build and run with default parameters"
	@echo "  make run-hires    - Build and run with high resolution"
	@echo "  make help         - Show this help message"

# Debug build
debug: CXXFLAGS = -std=c++17 -g -O0 -Wall -Wextra -fopenmp
debug: clean $(TARGET)
	@echo "Debug build complete"

.PHONY: all clean clean-output distclean run run-hires help debug
