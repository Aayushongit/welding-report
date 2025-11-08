#ifndef WELDING_SIMULATION_H
#define WELDING_SIMULATION_H

#include <vector>
#include <string>
#include <memory>

// Configuration structure for simulation parameters
struct SimulationConfig {
    // Domain and mesh
    double Lx = 0.15;          // Length in x (m)
    double Ly = 0.10;          // Length in y (m)
    double thickness = 0.006;  // Plate thickness (m)
    int nx = 151;              // Grid points in x
    int ny = 101;              // Grid points in y

    // Material 1 properties (Mild Steel)
    std::string mat_1_name = "Mild Steel";
    double mat_1_rho = 7850.0;   // Density (kg/m³)
    double mat_1_cp = 500.0;     // Specific heat (J/kg·K)
    double mat_1_k = 45.0;       // Thermal conductivity (W/m·K)
    double mat_1_T_melt = 1811.0;  // Melting temperature (K)
    double mat_1_T_crit = 1273.0;  // Critical temperature (K)

    // Material 2 properties (Stainless Steel 304)
    std::string mat_2_name = "Stainless Steel 304";
    double mat_2_rho = 7900.0;
    double mat_2_cp = 500.0;
    double mat_2_k = 16.3;
    double mat_2_T_melt = 1723.0;
    double mat_2_T_crit = 1273.0;

    // Heat source parameters
    double V = 25.0;           // Voltage (V)
    double I = 150.0;          // Current (A)
    double eta = 0.85;         // Efficiency
    double v_weld = 0.006;     // Welding velocity (m/s)
    double x_start = 0.02;     // Starting position (m)
    double y_arc = 0.0;        // Arc position in y (m)

    // Goldak double ellipsoid parameters
    double a = 0.005;          // Semi-axis in x (m)
    double b = 0.004;          // Semi-axis in y (m)
    double cf = 0.003;         // Front quadrant depth (m)
    double cr = 0.010;         // Rear quadrant depth (m)
    double ff = 0.6;           // Front fraction
    double fr = 1.4;           // Rear fraction

    // Simulation parameters
    double T0 = 293.0;         // Ambient temperature (K)
    double h_conv = 20.0;      // Convection coefficient (W/m²·K)
    double dt = 0.02;          // Time step (s)
    double theta = 0.5;        // Crank-Nicolson parameter (0.5 = centered)

    // Process parameters
    std::string weld_process = "TIG";  // TIG or Electrode
    bool use_gas = true;
    double snapshot_time = -1.0;       // Time for snapshot (-1 = disabled)

    // Video generation parameters
    bool save_video_frames = false;    // Enable video frame saving
    int video_frames_per_second = 10;  // FPS for video output
};

// Material class
class Material {
public:
    std::string name;
    double rho;        // Density
    double cp;         // Specific heat
    double k;          // Thermal conductivity
    double alpha;      // Thermal diffusivity
    double T_melt;     // Melting temperature
    double T_crit;     // Critical temperature (HAZ boundary)

    Material(const std::string& name, double rho, double cp, double k,
             double T_melt, double T_crit);

    // Temperature-dependent properties
    double get_k(double T) const;
    double get_cp(double T) const;
    double get_rho(double T) const;
};

// Main simulation class
class WeldingSimulation {
public:
    WeldingSimulation(const SimulationConfig& config);
    ~WeldingSimulation();

    // Run the simulation
    void run();

    // Export results
    void exportResults(const std::string& prefix = "") const;

    // Export video frame (called during simulation)
    void exportVideoFrame(int frame_number, double current_time);

private:
    SimulationConfig config_;
    std::unique_ptr<Material> mat_1_;
    std::unique_ptr<Material> mat_2_;

    // Grid
    int nx_, ny_, N_;
    double dx_, dy_;
    double midpoint_;
    std::vector<double> x_, y_;
    std::vector<double> X_, Y_;  // Meshgrid (row-major)

    // Temperature fields
    std::vector<double> T_;      // Current temperature
    std::vector<double> T_max_;  // Peak temperature

    // Time parameters
    double t_end_;
    int nt_;

    // Derived parameters
    double Q_total_;    // Total heat input
    double T_melt_;     // Average melting temperature
    double T_crit_;     // Average critical temperature

    // Monitoring
    std::vector<std::pair<int, int>> monitor_pts_;
    std::vector<std::vector<double>> T_history_;
    std::vector<double> time_history_;

    // Helper functions
    void initializeGrid();
    void initializeMaterials();
    void setupMonitoringPoints();

    // Index conversion: (i, j) -> linear index
    inline int idx(int i, int j) const { return j * nx_ + i; }

    // Compute Goldak heat flux
    void computeGoldakHeatFlux(double x_arc, std::vector<double>& q_surf) const;

    // Compute material properties for all grid points
    void computeMaterialProperties(const std::vector<double>& T_vec,
                                  std::vector<double>& k_arr,
                                  std::vector<double>& cp_arr,
                                  std::vector<double>& rho_arr) const;

    // Solve one time step
    void solveTimeStep(double t, const std::vector<double>& Qvol);

    // Apply boundary conditions (Dirichlet)
    inline bool isBoundary(int i, int j) const {
        return (i == 0 || i == nx_ - 1 || j == 0 || j == ny_ - 1);
    }

    // Update monitoring points
    void updateMonitoring(double t);

    // Compute zones
    void computeZones(std::vector<bool>& fusion_zone,
                     std::vector<bool>& HAZ_zone) const;

    // Print statistics
    void printStatistics() const;
};

#endif // WELDING_SIMULATION_H
