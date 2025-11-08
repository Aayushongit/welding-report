/*
 * sim-welding-tig.cpp
 * High-performance TIG welding simulation with video output
 * Optimized TIG parameters with Goldak's double ellipsoid model
 *
 * Compile: g++ -O3 -fopenmp -march=native sim-welding-tig.cpp -o sim-welding-tig
 * Run: ./sim-welding-tig
 */

#include <iostream>
#include <vector>
#include <cmath>
#include <fstream>
#include <chrono>
#include <iomanip>
#include <algorithm>
#include <sstream>
#include <omp.h>

// ==================== TIG Welding Configuration ====================
struct TIGConfig {
    // Domain and mesh
    double Lx = 0.15;           // Domain length (m)
    double Ly = 0.10;           // Domain width (m)
    double thickness = 0.006;   // Plate thickness (m)
    int nx = 151;               // Grid points in x
    int ny = 101;               // Grid points in y

    // Material 1: Mild Steel
    double mat_1_rho = 7850.0;  // Density (kg/m³)
    double mat_1_cp = 500.0;    // Specific heat (J/kg·K)
    double mat_1_k = 45.0;      // Thermal conductivity (W/m·K)
    double mat_1_T_melt = 1811.0; // Melting temperature (K)
    double mat_1_T_crit = 1273.0; // Critical HAZ temperature (K)

    // Material 2: Stainless Steel 304
    double mat_2_rho = 7900.0;
    double mat_2_cp = 500.0;
    double mat_2_k = 16.3;
    double mat_2_T_melt = 1723.0;
    double mat_2_T_crit = 1273.0;

    // TIG Welding Parameters (GTAW - Gas Tungsten Arc Welding)
    double V = 25.0;            // Arc voltage (V) - Typical TIG: 10-30V
    double I = 150.0;           // Welding current (A) - Typical TIG: 100-200A
    double eta = 0.75;          // Arc efficiency (TIG: 0.7-0.8, higher than SMAW)
    double v_weld = 0.006;      // Travel speed (m/s) = 6 mm/s = 360 mm/min
    double x_start = 0.02;      // Start position (m)
    double y_arc = 0.0;         // Arc centerline

    // Goldak Double Ellipsoid Parameters (calibrated for TIG)
    // TIG produces narrower, more concentrated heat input than SMAW
    double a = 0.004;           // Width parameter (m) - narrower for TIG
    double b = 0.003;           // Depth parameter (m) - shallow penetration
    double cf = 0.003;          // Front length (m) - shorter for TIG
    double cr = 0.008;          // Rear length (m) - TIG has moderate tail
    double ff = 0.6;            // Front heat fraction
    double fr = 1.4;            // Rear heat fraction (ff + fr = 2.0)

    // Simulation parameters
    double T0 = 293.0;          // Ambient temperature (K) = 20°C
    double dt = 0.02;           // Time step (s)
    double theta = 0.5;         // Crank-Nicolson parameter
    int output_interval = 50;   // Progress output frequency
    int frame_interval = 10;    // Video frame capture interval
};

// ==================== Material Properties ====================
inline double get_k(double T, double k_base, double T_crit, double T_melt) {
    if (T < T_crit) return k_base;
    if (T < T_melt) return k_base * (1.0 + (T - T_crit) / (T_melt - T_crit) * 0.1);
    return k_base * 1.1;
}

inline double get_cp(double T, double cp_base, double T_crit, double T_melt) {
    if (T < T_crit) return cp_base;
    if (T < T_melt) return cp_base * (1.0 + (T - T_crit) / (T_melt - T_crit) * 0.2);
    return cp_base * 1.2;
}

inline double get_rho(double T, double rho_base, double T_crit, double T_melt) {
    if (T < T_crit) return rho_base;
    if (T < T_melt) return rho_base * (1.0 - (T - T_crit) / (T_melt - T_crit) * 0.05);
    return rho_base * 0.95;
}

// ==================== Goldak Heat Flux (TIG-optimized) ====================
void goldak_heat_flux(const std::vector<double>& X, const std::vector<double>& Y,
                      double x_arc, double y_arc, double Q,
                      double a, double b, double cf, double cr, double ff, double fr,
                      int nx, int ny, std::vector<double>& q) {
    const double a_sq = a * a;
    const double b_sq = b * b;
    const double cf_sq = cf * cf;
    const double cr_sq = cr * cr;
    const double PI = 3.14159265358979323846;
    const double SQRT_PI = std::sqrt(PI);

    // Goldak coefficients for double ellipsoid
    const double coeff_f = (6.0 * ff * Q) / (a * b * cf * PI * SQRT_PI);
    const double coeff_r = (6.0 * fr * Q) / (a * b * cr * PI * SQRT_PI);

    #pragma omp parallel for collapse(2) schedule(static)
    for (int j = 0; j < ny; j++) {
        for (int i = 0; i < nx; i++) {
            int idx = j * nx + i;
            double xi = X[idx] - x_arc;
            double eta = Y[idx] - y_arc;
            double eta_sq = eta * eta;

            if (xi >= 0) {
                // Front ellipsoid
                double exp_arg = -3.0 * (xi * xi / cf_sq + eta_sq / b_sq);
                q[idx] = coeff_f * std::exp(exp_arg);
            } else {
                // Rear ellipsoid
                double exp_arg = -3.0 * (xi * xi / cr_sq + eta_sq / b_sq);
                q[idx] = coeff_r * std::exp(exp_arg);
            }
        }
    }
}

// ==================== TIG Welding Simulator ====================
class TIGSimulator {
private:
    TIGConfig config;
    int N;
    double dx, dy;
    double midpoint;

    std::vector<double> X, Y;
    std::vector<double> T, T_max;
    std::vector<double> q_surf, Q_vol;
    std::vector<double> k_arr, cp_arr, rho_arr, alpha_arr;

    std::vector<int> frame_steps;  // Steps when frames are saved

public:
    TIGSimulator(const TIGConfig& cfg) : config(cfg) {
        N = config.nx * config.ny;
        dx = config.Lx / (config.nx - 1);
        dy = config.Ly / (config.ny - 1);
        midpoint = config.Lx / 2.0;

        // Allocate memory
        X.resize(N);
        Y.resize(N);
        T.resize(N, config.T0);
        T_max.resize(N, config.T0);
        q_surf.resize(N, 0.0);
        Q_vol.resize(N, 0.0);
        k_arr.resize(N);
        cp_arr.resize(N);
        rho_arr.resize(N);
        alpha_arr.resize(N);

        // Initialize mesh
        #pragma omp parallel for collapse(2)
        for (int j = 0; j < config.ny; j++) {
            for (int i = 0; i < config.nx; i++) {
                int idx = j * config.nx + i;
                X[idx] = i * dx;
                Y[idx] = -config.Ly / 2.0 + j * dy;
            }
        }

        std::cout << "\n=== TIG Welding Simulation Setup ===" << std::endl;
        std::cout << "Grid: " << config.nx << " x " << config.ny << " nodes" << std::endl;
        std::cout << "Resolution: dx=" << dx*1000 << " mm, dy=" << dy*1000 << " mm" << std::endl;
        std::cout << "Domain: " << config.Lx*1000 << " mm x " << config.Ly*1000 << " mm" << std::endl;
    }

    void compute_material_properties() {
        #pragma omp parallel for
        for (int idx = 0; idx < N; idx++) {
            double x = X[idx];
            double temp = T[idx];

            double k_val, cp_val, rho_val;

            if (x < midpoint) {
                k_val = get_k(temp, config.mat_1_k, config.mat_1_T_crit, config.mat_1_T_melt);
                cp_val = get_cp(temp, config.mat_1_cp, config.mat_1_T_crit, config.mat_1_T_melt);
                rho_val = get_rho(temp, config.mat_1_rho, config.mat_1_T_crit, config.mat_1_T_melt);
            } else {
                k_val = get_k(temp, config.mat_2_k, config.mat_2_T_crit, config.mat_2_T_melt);
                cp_val = get_cp(temp, config.mat_2_cp, config.mat_2_T_crit, config.mat_2_T_melt);
                rho_val = get_rho(temp, config.mat_2_rho, config.mat_2_T_crit, config.mat_2_T_melt);
            }

            k_arr[idx] = k_val;
            cp_arr[idx] = cp_val;
            rho_arr[idx] = rho_val;
            alpha_arr[idx] = k_val / (rho_val * cp_val);
        }
    }

    void apply_heat_source(double t) {
        double x_arc = config.x_start + config.v_weld * t;

        if (x_arc <= config.Lx) {
            double Q_total = config.eta * config.V * config.I;
            goldak_heat_flux(X, Y, x_arc, config.y_arc, Q_total,
                           config.a, config.b, config.cf, config.cr, config.ff, config.fr,
                           config.nx, config.ny, q_surf);

            #pragma omp parallel for
            for (int i = 0; i < N; i++) {
                Q_vol[i] = q_surf[i];
            }
        } else {
            #pragma omp parallel for
            for (int i = 0; i < N; i++) {
                Q_vol[i] = 0.0;
            }
        }
    }

    void time_step_explicit() {
        std::vector<double> T_new(N);

        #pragma omp parallel for
        for (int j = 1; j < config.ny - 1; j++) {
            for (int i = 1; i < config.nx - 1; i++) {
                int idx = j * config.nx + i;
                int idx_xp = idx + 1;
                int idx_xm = idx - 1;
                int idx_yp = idx + config.nx;
                int idx_ym = idx - config.nx;

                double alpha = alpha_arr[idx];
                double d2Tdx2 = (T[idx_xp] - 2.0 * T[idx] + T[idx_xm]) / (dx * dx);
                double d2Tdy2 = (T[idx_yp] - 2.0 * T[idx] + T[idx_ym]) / (dy * dy);

                double heat_source = Q_vol[idx] / (rho_arr[idx] * cp_arr[idx]);

                T_new[idx] = T[idx] + config.dt * (alpha * (d2Tdx2 + d2Tdy2) + heat_source);
            }
        }

        // Boundary conditions
        #pragma omp parallel for
        for (int i = 0; i < config.nx; i++) {
            T_new[i] = config.T0;
            T_new[(config.ny - 1) * config.nx + i] = config.T0;
        }

        #pragma omp parallel for
        for (int j = 0; j < config.ny; j++) {
            T_new[j * config.nx] = config.T0;
            T_new[j * config.nx + config.nx - 1] = config.T0;
        }

        // Update temperature
        #pragma omp parallel for
        for (int i = 0; i < N; i++) {
            T[i] = T_new[i];
            if (T[i] > T_max[i]) {
                T_max[i] = T[i];
            }
        }
    }

    void save_frame(int step, double t) {
        std::ostringstream filename;
        filename << "output_cpp/frames/frame_" << std::setw(5) << std::setfill('0') << step << ".csv";

        std::ofstream file(filename.str());
        file << std::fixed << std::setprecision(6);

        for (int j = 0; j < config.ny; j++) {
            for (int i = 0; i < config.nx; i++) {
                int idx = j * config.nx + i;
                file << T[idx];
                if (i < config.nx - 1) file << ",";
            }
            file << "\n";
        }
        file.close();
    }

    void run_simulation() {
        double Q_total = config.eta * config.V * config.I;
        double t_end = (config.Lx - config.x_start) / config.v_weld + 10.0;
        int nt = static_cast<int>(std::ceil(t_end / config.dt));

        std::cout << "\n=== TIG Welding Parameters ===" << std::endl;
        std::cout << "Voltage: " << config.V << " V" << std::endl;
        std::cout << "Current: " << config.I << " A" << std::endl;
        std::cout << "Arc efficiency: " << config.eta * 100 << "%" << std::endl;
        std::cout << "Heat input: " << Q_total << " W (" << Q_total/1000.0 << " kW)" << std::endl;
        std::cout << "Travel speed: " << config.v_weld * 1000 << " mm/s ("
                  << config.v_weld * 60000 << " mm/min)" << std::endl;
        std::cout << "Heat input per length: " << Q_total / config.v_weld / 1000.0 << " kJ/mm" << std::endl;

        std::cout << "\n=== Goldak Parameters (TIG-optimized) ===" << std::endl;
        std::cout << "Width (a): " << config.a * 1000 << " mm" << std::endl;
        std::cout << "Depth (b): " << config.b * 1000 << " mm" << std::endl;
        std::cout << "Front length (cf): " << config.cf * 1000 << " mm" << std::endl;
        std::cout << "Rear length (cr): " << config.cr * 1000 << " mm" << std::endl;

        std::cout << "\n=== Simulation Info ===" << std::endl;
        std::cout << "Time steps: " << nt << std::endl;
        std::cout << "Simulation duration: " << t_end << " s" << std::endl;
        std::cout << "OpenMP threads: " << omp_get_max_threads() << std::endl;

        // Create output directories
        system("mkdir -p output_cpp/frames");

        auto start_time = std::chrono::high_resolution_clock::now();

        for (int step = 1; step <= nt; step++) {
            double t = step * config.dt;

            apply_heat_source(t);
            compute_material_properties();
            time_step_explicit();

            // Save frames for video
            if (step % config.frame_interval == 0 || step == nt) {
                save_frame(step, t);
                frame_steps.push_back(step);
            }

            // Progress output
            if (step % config.output_interval == 0 || step == nt) {
                double x_arc = config.x_start + config.v_weld * t;
                double T_max_current = *std::max_element(T.begin(), T.end());

                std::cout << "Step " << std::setw(5) << step << "/" << nt
                         << " | t=" << std::fixed << std::setprecision(2) << t << "s"
                         << " | Arc=" << std::setprecision(1) << x_arc * 1000 << "mm"
                         << " | T_max=" << std::setprecision(0) << T_max_current << "K"
                         << " (" << (T_max_current - 273.15) << "°C)"
                         << std::endl;
            }
        }

        auto end_time = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);

        std::cout << "\n=== Simulation Complete ===" << std::endl;
        std::cout << "Computation time: " << duration.count() / 1000.0 << " seconds" << std::endl;
        std::cout << "Time per step: " << duration.count() / static_cast<double>(nt) << " ms" << std::endl;
        std::cout << "Frames saved: " << frame_steps.size() << std::endl;

        analyze_results();
        save_results();
    }

    void analyze_results() {
        double T_melt = (config.mat_1_T_melt + config.mat_2_T_melt) / 2.0;
        double T_crit = (config.mat_1_T_crit + config.mat_2_T_crit) / 2.0;

        int fusion_count = 0;
        int haz_count = 0;
        double peak_temp = *std::max_element(T_max.begin(), T_max.end());

        #pragma omp parallel for reduction(+:fusion_count, haz_count)
        for (int i = 0; i < N; i++) {
            if (T_max[i] >= T_melt) {
                fusion_count++;
            } else if (T_max[i] >= T_crit) {
                haz_count++;
            }
        }

        double cell_area = dx * dy;
        double fusion_area = fusion_count * cell_area;
        double haz_area = haz_count * cell_area;

        std::cout << "\n=== Weld Analysis ===" << std::endl;
        std::cout << "Peak temperature: " << std::fixed << std::setprecision(1)
                  << peak_temp << " K (" << (peak_temp - 273.15) << " °C)" << std::endl;
        std::cout << "Fusion zone area: " << fusion_area * 1e6 << " mm²" << std::endl;
        std::cout << "HAZ area: " << haz_area * 1e6 << " mm²" << std::endl;
        std::cout << "Total affected area: " << (fusion_area + haz_area) * 1e6 << " mm²" << std::endl;
    }

    void save_results() {
        std::ofstream file("output_cpp/weld_results.csv");
        file << "x,y,T_max,T_final\n";
        file << std::fixed << std::setprecision(6);

        for (int j = 0; j < config.ny; j++) {
            for (int i = 0; i < config.nx; i++) {
                int idx = j * config.nx + i;
                file << X[idx] << "," << Y[idx] << "," << T_max[idx] << "," << T[idx] << "\n";
            }
        }
        file.close();

        std::ofstream cfg_file("output_cpp/weld_config.txt");
        cfg_file << "nx=" << config.nx << "\n";
        cfg_file << "ny=" << config.ny << "\n";
        cfg_file << "Lx=" << config.Lx << "\n";
        cfg_file << "Ly=" << config.Ly << "\n";
        cfg_file << "T_melt_1=" << config.mat_1_T_melt << "\n";
        cfg_file << "T_melt_2=" << config.mat_2_T_melt << "\n";
        cfg_file << "T_crit_1=" << config.mat_1_T_crit << "\n";
        cfg_file << "T_crit_2=" << config.mat_2_T_crit << "\n";
        cfg_file << "T0=" << config.T0 << "\n";
        cfg_file << "midpoint=" << midpoint << "\n";
        cfg_file.close();

        std::cout << "\nResults saved:" << std::endl;
        std::cout << "  - output_cpp/weld_results.csv" << std::endl;
        std::cout << "  - output_cpp/weld_config.txt" << std::endl;
        std::cout << "  - output_cpp/frames/*.csv (" << frame_steps.size() << " frames)" << std::endl;
    }
};

// ==================== Main ====================
int main(int argc, char* argv[]) {
    std::cout << "============================================" << std::endl;
    std::cout << "  TIG Welding Simulation (C++ + OpenMP)" << std::endl;
    std::cout << "  Goldak's Double Ellipsoid Model" << std::endl;
    std::cout << "============================================" << std::endl;

    if (argc > 1) {
        int num_threads = std::atoi(argv[1]);
        omp_set_num_threads(num_threads);
    }

    TIGConfig config;
    TIGSimulator simulator(config);
    simulator.run_simulation();

    std::cout << "\n=== Next Steps ===" << std::endl;
    std::cout << "1. Generate plots: python3 plot_weld_results.py" << std::endl;
    std::cout << "2. Create video: python3 create_video.py" << std::endl;

    return 0;
}
