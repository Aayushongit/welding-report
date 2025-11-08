#include "WeldingSimulation.h"
#include <iostream>
#include <cstring>
#include <sys/stat.h>
#include <omp.h>

void printUsage(const char* program_name) {
    std::cout << "Usage: " << program_name << " [options]" << std::endl;
    std::cout << "\nProcess Options:" << std::endl;
    std::cout << "  --weld_process <TIG|Electrode>  Welding process (default: TIG)" << std::endl;
    std::cout << "  --use_gas                       Enable shielding gas (default: enabled)" << std::endl;
    std::cout << "  --no-gas                        Disable shielding gas" << std::endl;
    std::cout << "\nPhysical Parameters:" << std::endl;
    std::cout << "  --current <A>                   Welding current in Amperes (default: 150)" << std::endl;
    std::cout << "  --voltage <V>                   Arc voltage in Volts (default: 25)" << std::endl;
    std::cout << "  --speed <m/s>                   Welding speed in m/s (default: 0.006)" << std::endl;
    std::cout << "\nMaterial 1 Properties (Mild Steel):" << std::endl;
    std::cout << "  --mat1_k <W/mK>                 Thermal conductivity (default: 45.0)" << std::endl;
    std::cout << "  --mat1_cp <J/kgK>               Specific heat (default: 500.0)" << std::endl;
    std::cout << "  --mat1_rho <kg/m3>              Density (default: 7850.0)" << std::endl;
    std::cout << "  --mat1_Tmelt <K>                Melting temperature (default: 1811.0)" << std::endl;
    std::cout << "\nMaterial 2 Properties (Stainless Steel 304):" << std::endl;
    std::cout << "  --mat2_k <W/mK>                 Thermal conductivity (default: 16.3)" << std::endl;
    std::cout << "  --mat2_cp <J/kgK>               Specific heat (default: 500.0)" << std::endl;
    std::cout << "  --mat2_rho <kg/m3>              Density (default: 7900.0)" << std::endl;
    std::cout << "  --mat2_Tmelt <K>                Melting temperature (default: 1723.0)" << std::endl;
    std::cout << "\nVideo Options:" << std::endl;
    std::cout << "  --save_video                    Enable video frame saving" << std::endl;
    std::cout << "  --video_fps <fps>               Video frames per second (default: 10)" << std::endl;
    std::cout << "\nOther Options:" << std::endl;
    std::cout << "  --snapshot_time <seconds>       Time for snapshot (default: -1, disabled)" << std::endl;
    std::cout << "  --help                          Show this help message" << std::endl;
}

void createOutputDirectory() {
    struct stat info;
    if (stat("output", &info) != 0) {
        // Directory doesn't exist, create it
        #ifdef _WIN32
            mkdir("output");
        #else
            mkdir("output", 0755);
        #endif
        std::cout << "Created output directory." << std::endl;
    }
}

void createVideoFramesDirectory() {
    struct stat info;
    if (stat("output/video_frames", &info) != 0) {
        // Directory doesn't exist, create it
        #ifdef _WIN32
            mkdir("output/video_frames");
        #else
            mkdir("output/video_frames", 0755);
        #endif
        std::cout << "Created output/video_frames directory." << std::endl;
    }
}

int main(int argc, char* argv[]) {
    std::cout << "=== Welding Simulation (C++ with OpenMP) ===" << std::endl;
    std::cout << "OpenMP Max Threads: " << omp_get_max_threads() << std::endl;

    // Default configuration
    SimulationConfig config;

    // Parse command line arguments
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--help") == 0) {
            printUsage(argv[0]);
            return 0;
        } else if (strcmp(argv[i], "--weld_process") == 0 && i + 1 < argc) {
            config.weld_process = argv[++i];
            if (config.weld_process != "TIG" && config.weld_process != "Electrode") {
                std::cerr << "Error: Invalid weld_process. Use 'TIG' or 'Electrode'." << std::endl;
                return 1;
            }
        } else if (strcmp(argv[i], "--use_gas") == 0) {
            config.use_gas = true;
        } else if (strcmp(argv[i], "--no-gas") == 0) {
            config.use_gas = false;
        } else if (strcmp(argv[i], "--snapshot_time") == 0 && i + 1 < argc) {
            config.snapshot_time = std::stod(argv[++i]);
        }
        // Physical parameters
        else if (strcmp(argv[i], "--current") == 0 && i + 1 < argc) {
            config.I = std::stod(argv[++i]);
        } else if (strcmp(argv[i], "--voltage") == 0 && i + 1 < argc) {
            config.V = std::stod(argv[++i]);
        } else if (strcmp(argv[i], "--speed") == 0 && i + 1 < argc) {
            config.v_weld = std::stod(argv[++i]);
        }
        // Material 1 properties
        else if (strcmp(argv[i], "--mat1_k") == 0 && i + 1 < argc) {
            config.mat_1_k = std::stod(argv[++i]);
        } else if (strcmp(argv[i], "--mat1_cp") == 0 && i + 1 < argc) {
            config.mat_1_cp = std::stod(argv[++i]);
        } else if (strcmp(argv[i], "--mat1_rho") == 0 && i + 1 < argc) {
            config.mat_1_rho = std::stod(argv[++i]);
        } else if (strcmp(argv[i], "--mat1_Tmelt") == 0 && i + 1 < argc) {
            config.mat_1_T_melt = std::stod(argv[++i]);
        }
        // Material 2 properties
        else if (strcmp(argv[i], "--mat2_k") == 0 && i + 1 < argc) {
            config.mat_2_k = std::stod(argv[++i]);
        } else if (strcmp(argv[i], "--mat2_cp") == 0 && i + 1 < argc) {
            config.mat_2_cp = std::stod(argv[++i]);
        } else if (strcmp(argv[i], "--mat2_rho") == 0 && i + 1 < argc) {
            config.mat_2_rho = std::stod(argv[++i]);
        } else if (strcmp(argv[i], "--mat2_Tmelt") == 0 && i + 1 < argc) {
            config.mat_2_T_melt = std::stod(argv[++i]);
        }
        // Video options
        else if (strcmp(argv[i], "--save_video") == 0) {
            config.save_video_frames = true;
        } else if (strcmp(argv[i], "--video_fps") == 0 && i + 1 < argc) {
            config.video_frames_per_second = std::stoi(argv[++i]);
        } else {
            std::cerr << "Error: Unknown option '" << argv[i] << "'" << std::endl;
            printUsage(argv[0]);
            return 1;
        }
    }

    // Create output directories
    createOutputDirectory();
    if (config.save_video_frames) {
        createVideoFramesDirectory();
    }

    // Create and run simulation
    try {
        WeldingSimulation sim(config);
        sim.run();
        sim.exportResults();

        std::cout << "\n=== Simulation Complete ===" << std::endl;
        std::cout << "Results saved to output/ directory" << std::endl;
        std::cout << "  - simulation_results.csv: Temperature field data" << std::endl;
        std::cout << "  - thermal_history.csv: Temperature history at monitoring points" << std::endl;

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
