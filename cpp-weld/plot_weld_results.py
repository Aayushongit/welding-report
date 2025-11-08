#!/usr/bin/env python3
"""
Visualization script for C++ welding simulation results
Reads weld_results.csv and creates comprehensive plots
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import os

def read_config(filename='output_cpp/weld_config.txt'):
    """Read configuration from file"""
    config = {}
    with open(filename, 'r') as f:
        for line in f:
            key, value = line.strip().split('=')
            config[key] = float(value)
    return config

def read_results(filename='output_cpp/weld_results.csv'):
    """Read simulation results"""
    data = np.loadtxt(filename, delimiter=',', skiprows=1)
    x = data[:, 0]
    y = data[:, 1]
    T_max = data[:, 2]
    T_final = data[:, 3]
    return x, y, T_max, T_final

def create_plots():
    """Create comprehensive visualization"""
    print("Loading simulation results...")

    # Read data
    config = read_config()
    x, y, T_max, T_final = read_results()

    nx = int(config['nx'])
    ny = int(config['ny'])
    Lx = config['Lx']
    Ly = config['Ly']
    T_melt = (config['T_melt_1'] + config['T_melt_2']) / 2.0
    T_crit = (config['T_crit_1'] + config['T_crit_2']) / 2.0
    T0 = config['T0']
    midpoint = config['midpoint']

    # Reshape data
    X = x.reshape(ny, nx)
    Y = y.reshape(ny, nx)
    T_max_2d = T_max.reshape(ny, nx)
    T_final_2d = T_final.reshape(ny, nx)

    # Create fusion and HAZ masks
    fusion_zone = T_max_2d >= T_melt
    HAZ_zone = (T_max_2d >= T_crit) & (T_max_2d < T_melt)

    # Calculate areas
    dx = Lx / (nx - 1)
    dy = Ly / (ny - 1)
    cell_area = dx * dy
    fusion_area = fusion_zone.sum() * cell_area * 1e6  # mm²
    haz_area = HAZ_zone.sum() * cell_area * 1e6  # mm²

    print(f"Grid: {nx} x {ny}")
    print(f"Peak temperature: {T_max.max():.1f} K ({T_max.max()-273.15:.1f} °C)")
    print(f"Fusion zone area: {fusion_area:.2f} mm²")
    print(f"HAZ area: {haz_area:.2f} mm²")

    # Create output directory
    os.makedirs('output_cpp', exist_ok=True)

    # ===== Plot 1: Peak Temperature with Isotherms =====
    print("Creating Plot 1: Peak Temperature with Isotherms...")
    fig1, ax1 = plt.subplots(figsize=(12, 6))

    im1 = ax1.contourf(X*1000, Y*1000, T_max_2d, levels=50, cmap='hot')

    # Add critical isotherms
    contours = ax1.contour(X*1000, Y*1000, T_max_2d,
                           levels=[T_crit, T_melt],
                           colors=['cyan', 'white'],
                           linewidths=[2.5, 3.0],
                           linestyles=['--', '-'])
    ax1.clabel(contours, inline=True, fontsize=10, fmt='%d K')

    # Material interface
    ax1.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2, label='Material Interface')

    ax1.set_xlabel('x (mm)', fontsize=12)
    ax1.set_ylabel('y (mm)', fontsize=12)
    ax1.set_title(f'Peak Temperature Distribution\n(Cyan={T_crit:.0f} K / {T_crit-273.15:.0f} °C HAZ boundary, White={T_melt:.0f} K / {T_melt-273.15:.0f} °C Fusion boundary)', fontsize=14, fontweight='bold')
    plt.colorbar(im1, ax=ax1, label='Temperature (K)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('output_cpp/1_peak_temperature.png', dpi=300, bbox_inches='tight')

    # ===== Plot 2: Fusion Zone and HAZ =====
    print("Creating Plot 2: Fusion Zone and HAZ...")
    fig2, ax2 = plt.subplots(figsize=(12, 6))

    ax2.contourf(X*1000, Y*1000, T_max_2d, levels=30, cmap='gray', alpha=0.3)

    if fusion_zone.any():
        ax2.contourf(X*1000, Y*1000, fusion_zone.astype(float),
                    levels=[0.5, 1.5], colors=['red'], alpha=0.5)

    if HAZ_zone.any():
        ax2.contourf(X*1000, Y*1000, HAZ_zone.astype(float),
                    levels=[0.5, 1.5], colors=['orange'], alpha=0.4)

    ax2.contour(X*1000, Y*1000, T_max_2d, levels=[T_crit, T_melt],
               colors=['black', 'black'], linewidths=[2, 2.5])

    ax2.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2)
    ax2.set_xlabel('x (mm)', fontsize=12)
    ax2.set_ylabel('y (mm)', fontsize=12)
    ax2.set_title(f'Fusion Zone & HAZ\nFusion: {fusion_area:.2f} mm² | HAZ: {haz_area:.2f} mm²',
                 fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('output_cpp/2_fusion_haz.png', dpi=300, bbox_inches='tight')

    # ===== Plot 3: Centerline Temperature =====
    print("Creating Plot 3: Centerline Temperature Profile...")
    fig3, ax3 = plt.subplots(figsize=(12, 6))

    centerline_idx = ny // 2
    x_line = X[centerline_idx, :]
    T_max_line = T_max_2d[centerline_idx, :]
    T_final_line = T_final_2d[centerline_idx, :]

    ax3.plot(x_line*1000, T_max_line, 'r-', linewidth=2.5, label='Peak T')
    ax3.plot(x_line*1000, T_final_line, 'b-', linewidth=2.0, label='Final T')

    ax3.axhline(T_melt, color='red', linestyle='--', linewidth=2, alpha=0.7, label=f'T_melt ({T_melt:.0f} K)')
    ax3.axhline(T_crit, color='orange', linestyle='--', linewidth=2, alpha=0.7, label=f'T_HAZ ({T_crit:.0f} K)')
    ax3.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2, label='Interface')

    ax3.fill_between(x_line*1000, T0, T_max_line, where=(T_max_line >= T_melt),
                     color='red', alpha=0.3, label='Fusion Zone')
    ax3.fill_between(x_line*1000, T0, T_max_line,
                     where=((T_max_line >= T_crit) & (T_max_line < T_melt)),
                     color='orange', alpha=0.3, label='HAZ')

    ax3.set_xlabel('x (mm)', fontsize=12)
    ax3.set_ylabel('Temperature (K)', fontsize=12)
    ax3.set_title('Centerline Temperature Profile', fontsize=14, fontweight='bold')
    ax3.legend(fontsize=10, loc='upper right')
    ax3.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('output_cpp/3_centerline_profile.png', dpi=300, bbox_inches='tight')

    # ===== Plot 4: Transverse Temperature Profile =====
    print("Creating Plot 4: Transverse Temperature Profile...")
    fig4, ax4 = plt.subplots(figsize=(10, 6))

    transverse_idx = int(nx * 0.5)
    y_line = Y[:, transverse_idx]
    T_transverse = T_max_2d[:, transverse_idx]

    ax4.plot(y_line*1000, T_transverse, 'r-', linewidth=2.5)
    ax4.axhline(T_melt, color='red', linestyle='--', linewidth=2)
    ax4.axhline(T_crit, color='orange', linestyle='--', linewidth=2)

    ax4.set_xlabel('y (mm)', fontsize=12)
    ax4.set_ylabel('Peak Temperature (K)', fontsize=12)
    ax4.set_title('Transverse Temperature Profile at Weld Center', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('output_cpp/4_transverse_profile.png', dpi=300, bbox_inches='tight')

    # ===== Plot 5: 3D Peak Temperature (Interactive) =====
    print("Creating Plot 5: 3D Peak Temperature (Interactive)...")
    try:
        import plotly.graph_objects as go
        fig = go.Figure(data=[go.Surface(z=T_max_2d, x=X*1000, y=Y*1000, colorscale='hot', colorbar=dict(title='T (K)'))])
        fig.update_layout(title='3D Peak Temperature Distribution',
                          scene=dict(
                              xaxis_title='x (mm)',
                              yaxis_title='y (mm)',
                              zaxis_title='Temperature (K)',
                              aspectratio=dict(x=1, y=1, z=0.5),
                              camera_eye=dict(x=1.87, y=0.88, z=0.64)),
                          margin=dict(l=0, r=0, b=0, t=40))
        fig.write_html("output_cpp/5_3d_temperature.html")
        print("  -> Interactive 3D plot saved to output_cpp/5_3d_temperature.html")
    except ImportError:
        print("  -> Plotly not found. Skipping interactive 3D plot.")
        print("     To install: pip install plotly")
        print("     Falling back to static 3D plot...")
        fig5 = plt.figure(figsize=(14, 10))
        ax5 = fig5.add_subplot(111, projection='3d')
        surf = ax5.plot_surface(X*1000, Y*1000, T_max_2d, cmap='hot',
                               edgecolor='none', alpha=0.9)
        ax5.set_xlabel('x (mm)', fontsize=11)
        ax5.set_ylabel('y (mm)', fontsize=11)
        ax5.set_zlabel('Temperature (K)', fontsize=11)
        ax5.set_title('3D Peak Temperature Distribution', fontsize=14, fontweight='bold')
        fig5.colorbar(surf, ax=ax5, shrink=0.5, label='T (K)')
        ax5.view_init(elev=25, azim=45)
        plt.tight_layout()
        plt.savefig('output_cpp/5_3d_temperature.png', dpi=300, bbox_inches='tight')
        print("  -> Static 3D plot saved to output_cpp/5_3d_temperature.png")

    # ===== Plot 6: Weld Width Along Length =====
    print("Creating Plot 6: Weld Width Along Length...")
    fig6, ax6 = plt.subplots(figsize=(12, 6))

    if fusion_zone.any():
        weld_widths = []
        x_positions = []

        for i in range(nx):
            if fusion_zone[:, i].any():
                y_indices = np.where(fusion_zone[:, i])[0]
                if len(y_indices) > 1:
                    width = (Y[y_indices[-1], i] - Y[y_indices[0], i]) * 1000
                    weld_widths.append(width)
                    x_positions.append(X[0, i] * 1000)

        if weld_widths:
            ax6.plot(x_positions, weld_widths, 'b-o', linewidth=2, markersize=4, label='Weld Width')
            ax6.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2.5, label='Material Interface')
            avg_width = np.mean(weld_widths)
            ax6.axhline(avg_width, color='red', linestyle='--', linewidth=2,
                       label=f'Average: {avg_width:.2f} mm')

            ax6.set_xlabel('x (mm)', fontsize=12)
            ax6.set_ylabel('Weld Width (mm)', fontsize=12)
            ax6.set_title('Weld Width Along Length', fontsize=14, fontweight='bold')
            ax6.legend(fontsize=10)
            ax6.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('output_cpp/6_weld_width.png', dpi=300, bbox_inches='tight')

    # ===== Plot 7: Temperature Gradient Magnitude =====
    print("Creating Plot 7: Temperature Gradient...")
    fig7, ax7 = plt.subplots(figsize=(12, 6))

    dTdx, dTdy = np.gradient(T_max_2d, dx, dy)
    grad_magnitude = np.sqrt(dTdx**2 + dTdy**2)

    im7 = ax7.contourf(X*1000, Y*1000, grad_magnitude, levels=40, cmap='plasma')
    ax7.contour(X*1000, Y*1000, T_max_2d, levels=[T_crit, T_melt],
               colors=['cyan', 'white'], linewidths=2)
    ax7.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2)

    ax7.set_xlabel('x (mm)', fontsize=12)
    ax7.set_ylabel('y (mm)', fontsize=12)
    ax7.set_title('Temperature Gradient Magnitude', fontsize=14, fontweight='bold')
    plt.colorbar(im7, ax=ax7, label='|∇T| (K/m)')
    plt.tight_layout()
    plt.savefig('output_cpp/7_temperature_gradient.png', dpi=300, bbox_inches='tight')

    print("\n" + "="*60)
    print("All plots saved in 'output_cpp/' directory:")
    print("  1_peak_temperature.png")
    print("  2_fusion_haz.png")
    print("  3_centerline_profile.png")
    print("  4_transverse_profile.png")
    print("  5_3d_temperature.html (Interactive)")
    print("  5_3d_temperature.png (Static fallback)")
    print("  6_weld_width.png")
    print("  7_temperature_gradient.png")
    print("="*60)

    plt.show()

if __name__ == "__main__":
    create_plots()