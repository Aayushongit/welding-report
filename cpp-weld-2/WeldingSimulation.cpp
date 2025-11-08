#include "WeldingSimulation.h"
#include <cmath>
#include <iostream>
#include <fstream>
#include <iomanip>
#include <algorithm>
#include <chrono>
#include <omp.h>

// Material implementation
Material::Material(const std::string& name, double rho, double cp, double k,
                  double T_melt, double T_crit)
    : name(name), rho(rho), cp(cp), k(k), T_melt(T_melt), T_crit(T_crit) {
    alpha = k / (rho * cp);
}

double Material::get_k(double T) const {
    if (T < T_crit) {
        return k;
    } else if (T < T_melt) {
        return k * (1.0 + (T - T_crit) / (T_melt - T_crit) * 0.1);
    } else {
        return k * 1.1;
    }
}

double Material::get_cp(double T) const {
    if (T < T_crit) {
        return cp;
    } else if (T < T_melt) {
        return cp * (1.0 + (T - T_crit) / (T_melt - T_crit) * 0.2);
    } else {
        return cp * 1.2;
    }
}

double Material::get_rho(double T) const {
    if (T < T_crit) {
        return rho;
    } else if (T < T_melt) {
        return rho * (1.0 - (T - T_crit) / (T_melt - T_crit) * 0.05);
    } else {
        return rho * 0.95;
    }
}

// WeldingSimulation implementation
WeldingSimulation::WeldingSimulation(const SimulationConfig& config)
    : config_(config), nx_(config.nx), ny_(config.ny) {

    N_ = nx_ * ny_;
    midpoint_ = config_.Lx / 2.0;

    // Adjust efficiency based on welding process
    if (config_.weld_process == "TIG") {
        std::cout << "Simulating TIG welding." << std::endl;
        if (config_.use_gas) {
            std::cout << "Using shielding gas." << std::endl;
            config_.eta = 0.75;
        } else {
            std::cout << "Not using shielding gas." << std::endl;
            config_.eta = 0.65;
        }
    } else if (config_.weld_process == "Electrode") {
        std::cout << "Simulating Electrode welding." << std::endl;
        config_.eta = 0.85;
        if (config_.use_gas) {
            std::cout << "Warning: Gas is not typically used with electrode welding." << std::endl;
        }
    }

    Q_total_ = config_.eta * config_.V * config_.I;

    initializeGrid();
    initializeMaterials();
    setupMonitoringPoints();

    // Calculate time parameters
    t_end_ = (config_.Lx - config_.x_start) / config_.v_weld + 10.0;
    nt_ = static_cast<int>(std::ceil(t_end_ / config_.dt));

    // Initialize temperature fields
    T_.resize(N_, config_.T0);
    T_max_.resize(N_, config_.T0);

    std::cout << "Grid: " << nx_ << "x" << ny_ << ", Time steps: " << nt_ << std::endl;
    std::cout << "Materials: " << mat_1_->name << " | " << mat_2_->name << std::endl;
    std::cout << "Power: " << Q_total_ << "W, Speed: " << config_.v_weld * 1000.0 << "mm/s" << std::endl;
}

WeldingSimulation::~WeldingSimulation() = default;

void WeldingSimulation::initializeGrid() {
    x_.resize(nx_);
    y_.resize(ny_);
    X_.resize(N_);
    Y_.resize(N_);

    // Create 1D grids
    for (int i = 0; i < nx_; ++i) {
        x_[i] = i * config_.Lx / (nx_ - 1);
    }
    for (int j = 0; j < ny_; ++j) {
        y_[j] = -config_.Ly / 2.0 + j * config_.Ly / (ny_ - 1);
    }

    dx_ = x_[1] - x_[0];
    dy_ = y_[1] - y_[0];

    // Create 2D meshgrid (row-major: Y varies with row, X with column)
    #pragma omp parallel for collapse(2)
    for (int j = 0; j < ny_; ++j) {
        for (int i = 0; i < nx_; ++i) {
            int index = idx(i, j);
            X_[index] = x_[i];
            Y_[index] = y_[j];
        }
    }
}

void WeldingSimulation::initializeMaterials() {
    mat_1_ = std::make_unique<Material>(
        config_.mat_1_name, config_.mat_1_rho, config_.mat_1_cp,
        config_.mat_1_k, config_.mat_1_T_melt, config_.mat_1_T_crit
    );

    mat_2_ = std::make_unique<Material>(
        config_.mat_2_name, config_.mat_2_rho, config_.mat_2_cp,
        config_.mat_2_k, config_.mat_2_T_melt, config_.mat_2_T_crit
    );

    T_melt_ = (mat_1_->T_melt + mat_2_->T_melt) / 2.0;
    T_crit_ = (mat_1_->T_crit + mat_2_->T_crit) / 2.0;
}

void WeldingSimulation::setupMonitoringPoints() {
    // Three monitoring points: left, center, right
    monitor_pts_ = {
        {static_cast<int>(nx_ * 0.35), ny_ / 2},
        {nx_ / 2, ny_ / 2},
        {static_cast<int>(nx_ * 0.65), ny_ / 2}
    };

    T_history_.resize(monitor_pts_.size());
}

void WeldingSimulation::computeGoldakHeatFlux(double x_arc, std::vector<double>& q_surf) const {
    const double a = config_.a;
    const double b = config_.b;
    const double cf = config_.cf;
    const double cr = config_.cr;
    const double ff = config_.ff;
    const double fr = config_.fr;
    const double y_arc = config_.y_arc;

    const double a_sq = a * a;
    const double b_sq = b * b;
    const double coeff_f = (ff * Q_total_) / (a * b * M_PI);
    const double coeff_r = (fr * Q_total_) / (a * b * M_PI);

    q_surf.resize(N_);

    // Parallelize with OpenMP
    #pragma omp parallel for collapse(2)
    for (int j = 0; j < ny_; ++j) {
        for (int i = 0; i < nx_; ++i) {
            int index = idx(i, j);
            double xi = X_[index] - x_arc;
            double eta = Y_[index] - y_arc;
            double exp_arg = -xi * xi / a_sq - eta * eta / b_sq;

            if (xi >= 0) {
                q_surf[index] = coeff_f * std::exp(exp_arg);
            } else {
                q_surf[index] = coeff_r * std::exp(exp_arg);
            }
        }
    }
}

void WeldingSimulation::computeMaterialProperties(const std::vector<double>& T_vec,
                                                 std::vector<double>& k_arr,
                                                 std::vector<double>& cp_arr,
                                                 std::vector<double>& rho_arr) const {
    k_arr.resize(N_);
    cp_arr.resize(N_);
    rho_arr.resize(N_);

    // Parallelize material property computation
    #pragma omp parallel for
    for (int idx = 0; idx < N_; ++idx) {
        const Material* mat = (X_[idx] < midpoint_) ? mat_1_.get() : mat_2_.get();
        k_arr[idx] = mat->get_k(T_vec[idx]);
        cp_arr[idx] = mat->get_cp(T_vec[idx]);
        rho_arr[idx] = mat->get_rho(T_vec[idx]);
    }
}

void WeldingSimulation::solveTimeStep(double t, const std::vector<double>& Qvol) {
    // Get material properties
    std::vector<double> k_arr, cp_arr, rho_arr;
    computeMaterialProperties(T_, k_arr, cp_arr, rho_arr);

    // Create new temperature array
    std::vector<double> T_new(N_);

    const double dt = config_.dt;
    const double theta = config_.theta;

    // Maximum reasonable temperature for welding (prevents instability)
    const double T_MAX_REASONABLE = 5000.0;  // K (well above melting point)

    // Explicit finite difference with OpenMP
    // For simplicity, using explicit Euler for the heat equation
    // This is a simplified solver - full implicit would require sparse matrix solver

    #pragma omp parallel for collapse(2)
    for (int j = 0; j < ny_; ++j) {
        for (int i = 0; i < nx_; ++i) {
            int index = idx(i, j);

            // Boundary conditions: fixed temperature
            if (isBoundary(i, j)) {
                T_new[index] = config_.T0;
                continue;
            }

            // Interior points: explicit finite difference
            double alpha = k_arr[index] / (rho_arr[index] * cp_arr[index]);

            int idx_xm = idx(i - 1, j);
            int idx_xp = idx(i + 1, j);
            int idx_ym = idx(i, j - 1);
            int idx_yp = idx(i, j + 1);

            double d2T_dx2 = (T_[idx_xp] - 2.0 * T_[index] + T_[idx_xm]) / (dx_ * dx_);
            double d2T_dy2 = (T_[idx_yp] - 2.0 * T_[index] + T_[idx_ym]) / (dy_ * dy_);

            double heat_source = Qvol[index] / (rho_arr[index] * cp_arr[index]);

            // Calculate stability criterion (CFL condition)
            double dx_sq = dx_ * dx_;
            double dy_sq = dy_ * dy_;
            double stability_factor = alpha * dt * (1.0 / dx_sq + 1.0 / dy_sq);

            // For stability, we need: stability_factor < 0.5 for 2D explicit scheme
            // If unstable, limit the temperature change
            double max_dt_stable = 0.4 / (alpha * (1.0 / dx_sq + 1.0 / dy_sq));
            double dt_effective = std::min(dt, max_dt_stable);

            T_new[index] = T_[index] + dt_effective * (alpha * (d2T_dx2 + d2T_dy2) + heat_source);

            // Clamp to reasonable values to prevent numerical instability
            if (T_new[index] > T_MAX_REASONABLE) {
                T_new[index] = T_MAX_REASONABLE;
            } else if (T_new[index] < config_.T0) {
                T_new[index] = config_.T0;
            }
        }
    }

    // Update temperature
    T_ = T_new;

    // Update maximum temperature
    #pragma omp parallel for
    for (int idx = 0; idx < N_; ++idx) {
        T_max_[idx] = std::max(T_max_[idx], T_[idx]);
    }
}

void WeldingSimulation::updateMonitoring(double t) {
    time_history_.push_back(t);

    for (size_t k = 0; k < monitor_pts_.size(); ++k) {
        int i = monitor_pts_[k].first;
        int j = monitor_pts_[k].second;
        int index = idx(i, j);
        T_history_[k].push_back(T_[index]);
    }
}

void WeldingSimulation::run() {
    auto start_time = std::chrono::high_resolution_clock::now();

    double t = 0.0;
    bool snapshot_taken = false;
    int frame_counter = 0;
    int frame_interval = 1;  // Save every N steps for video

    // Calculate frame interval based on desired FPS
    if (config_.save_video_frames && config_.video_frames_per_second > 0) {
        double time_per_frame = 1.0 / config_.video_frames_per_second;
        frame_interval = std::max(1, static_cast<int>(time_per_frame / config_.dt));
        std::cout << "Video frames will be saved every " << frame_interval << " steps" << std::endl;
    }

    std::cout << "Running simulation..." << std::endl;

    for (int step = 1; step <= nt_; ++step) {
        t += config_.dt;

        // Update arc position
        double x_arc = config_.x_start + config_.v_weld * t;

        // Compute heat flux
        std::vector<double> q_surf;
        std::vector<double> Qvol(N_, 0.0);

        if (x_arc <= config_.Lx) {
            computeGoldakHeatFlux(x_arc, q_surf);

            // Convert surface flux to volumetric
            #pragma omp parallel for
            for (int idx = 0; idx < N_; ++idx) {
                Qvol[idx] = q_surf[idx] / config_.thickness;
            }
        }

        // Solve time step
        solveTimeStep(t, Qvol);

        // Update monitoring
        updateMonitoring(t);

        // Save video frame
        if (config_.save_video_frames && (step % frame_interval == 0 || step == nt_)) {
            exportVideoFrame(frame_counter, t);
            frame_counter++;
        }

        // Snapshot
        if (config_.snapshot_time > 0 && t >= config_.snapshot_time && !snapshot_taken) {
            std::cout << "Taking snapshot at t=" << t << "s" << std::endl;
            exportResults("_snapshot_" + std::to_string(static_cast<int>(t)) + "s");
            snapshot_taken = true;
        }

        // Progress indicator
        if (step % (nt_ / 10) == 0 || step == nt_) {
            std::cout << "Progress: " << (100 * step / nt_) << "%" << std::endl;
        }
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);

    std::cout << "Simulation completed in " << duration.count() / 1000.0 << "s" << std::endl;

    printStatistics();
}

void WeldingSimulation::computeZones(std::vector<bool>& fusion_zone,
                                    std::vector<bool>& HAZ_zone) const {
    fusion_zone.resize(N_);
    HAZ_zone.resize(N_);

    #pragma omp parallel for
    for (int idx = 0; idx < N_; ++idx) {
        fusion_zone[idx] = (T_max_[idx] >= T_melt_);
        HAZ_zone[idx] = (T_max_[idx] >= T_crit_ && T_max_[idx] < T_melt_);
    }
}

void WeldingSimulation::printStatistics() const {
    // Find maximum temperature
    double T_peak = *std::max_element(T_max_.begin(), T_max_.end());

    // Compute zones
    std::vector<bool> fusion_zone, HAZ_zone;
    computeZones(fusion_zone, HAZ_zone);

    int fusion_count = std::count(fusion_zone.begin(), fusion_zone.end(), true);
    int HAZ_count = std::count(HAZ_zone.begin(), HAZ_zone.end(), true);

    double cell_area = dx_ * dy_;
    double fusion_area = fusion_count * cell_area;
    double HAZ_area = HAZ_count * cell_area;

    std::cout << "\n=== Simulation Results ===" << std::endl;
    std::cout << "Peak Temperature: " << T_peak << " K" << std::endl;
    std::cout << "Fusion Zone Area: " << fusion_area * 1e6 << " mm²" << std::endl;
    std::cout << "HAZ Area: " << HAZ_area * 1e6 << " mm²" << std::endl;
}

void WeldingSimulation::exportResults(const std::string& prefix) const {
    std::string filename = "output/simulation_results" + prefix + ".csv";

    std::ofstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open file " << filename << std::endl;
        return;
    }

    file << std::setprecision(6) << std::fixed;

    // Write header
    file << "i,j,x,y,T_final,T_max" << std::endl;

    // Write data
    for (int j = 0; j < ny_; ++j) {
        for (int i = 0; i < nx_; ++i) {
            int index = idx(i, j);
            file << i << "," << j << ","
                 << x_[i] << "," << y_[j] << ","
                 << T_[index] << "," << T_max_[index] << std::endl;
        }
    }

    file.close();

    // Export thermal history
    std::string history_file = "output/thermal_history" + prefix + ".csv";
    std::ofstream hist_file(history_file);

    if (hist_file.is_open()) {
        hist_file << std::setprecision(6) << std::fixed;
        hist_file << "time";
        for (size_t k = 0; k < monitor_pts_.size(); ++k) {
            hist_file << ",T_pt" << k + 1;
        }
        hist_file << std::endl;

        for (size_t t = 0; t < time_history_.size(); ++t) {
            hist_file << time_history_[t];
            for (size_t k = 0; k < monitor_pts_.size(); ++k) {
                hist_file << "," << T_history_[k][t];
            }
            hist_file << std::endl;
        }
        hist_file.close();
    }

    std::cout << "Results exported to " << filename << " and " << history_file << std::endl;
}

void WeldingSimulation::exportVideoFrame(int frame_number, double current_time) {
    std::string filename = "output/video_frames/frame_" +
                          std::to_string(frame_number) + ".csv";

    std::ofstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open file " << filename << std::endl;
        return;
    }

    file << std::setprecision(6) << std::fixed;

    // Write header with metadata
    file << "# Frame: " << frame_number << ", Time: " << current_time << "s" << std::endl;
    file << "i,j,x,y,T" << std::endl;

    // Write current temperature data
    for (int j = 0; j < ny_; ++j) {
        for (int i = 0; i < nx_; ++i) {
            int index = idx(i, j);
            file << i << "," << j << ","
                 << x_[i] << "," << y_[j] << ","
                 << T_[index] << std::endl;
        }
    }

    file.close();
}
