#!/usr/bin/env python3
"""
Complete Visualization Script for C++ Welding Simulation Results
Generates all 17 plots from the original Python implementation
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
import os
import sys

def load_results(filename='output/simulation_results.csv'):
    """Load simulation results from CSV file."""
    if not os.path.exists(filename):
        print(f"Error: File {filename} not found.")
        print("Please run the simulation first: ./welding_sim")
        sys.exit(1)
    df = pd.read_csv(filename)
    return df

def load_thermal_history(filename='output/thermal_history.csv'):
    """Load thermal history from CSV file."""
    if not os.path.exists(filename):
        print(f"Warning: File {filename} not found.")
        return None
    df = pd.read_csv(filename)
    return df

def prepare_data(df):
    """Prepare data from CSV."""
    nx = df['i'].max() + 1
    ny = df['j'].max() + 1

    x = df['x'].values.reshape(ny, nx)[0, :]
    y = df['y'].values.reshape(ny, nx)[:, 0]
    T_final = df['T_final'].values.reshape(ny, nx)
    T_max = df['T_max'].values.reshape(ny, nx)

    # Replace inf and nan values with reasonable values
    T_final = np.nan_to_num(T_final, nan=293.0, posinf=5000.0, neginf=293.0)
    T_max = np.nan_to_num(T_max, nan=293.0, posinf=5000.0, neginf=293.0)

    X, Y = np.meshgrid(x, y)

    return x, y, X, Y, T_final, T_max, nx, ny

def save_all_plots(x, y, X, Y, T_final, T_max, df_history, nx, ny, output_dir='output'):
    """Generate all 17 plots matching the Python implementation."""

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Parameters
    T0 = 293.0
    T_crit = 1273.0
    T_melt = 1767.0
    midpoint = x[len(x)//2]
    dx = x[1] - x[0]
    dy = y[1] - y[0]

    # Compute zones
    fusion_zone = T_max >= T_melt
    HAZ_zone = (T_max >= T_crit) & (T_max < T_melt)

    # Isotherm levels
    isotherm_levels_detailed = np.array([400, 500, 600, 700, 800, 900, 1000, 1100, 1200,
                                         1273, 1400, 1500, 1600, 1767, 1900, 2000, 2100, 2200])
    isotherm_levels_detailed = isotherm_levels_detailed[isotherm_levels_detailed < T_max.max()]

    isotherm_colors = []
    isotherm_styles = []
    isotherm_widths = []

    for temp in isotherm_levels_detailed:
        if temp < T_crit:
            isotherm_colors.append('blue')
            isotherm_styles.append('-')
            isotherm_widths.append(1.0)
        elif temp < T_melt:
            isotherm_colors.append('orange')
            isotherm_styles.append('--')
            isotherm_widths.append(1.5)
        else:
            isotherm_colors.append('red')
            isotherm_styles.append('-')
            isotherm_widths.append(2.0)

    # PLOT 1: Detailed Temperature Isotherms
    print("Creating Plot 1: Detailed Temperature Isotherms...")
    fig1 = plt.figure(figsize=(10, 8))
    ax1 = fig1.add_subplot(111)
    levels_fill = np.linspace(T0, T_max.max(), 60)
    im1 = ax1.contourf(x*1000, y*1000, T_max, levels=levels_fill, cmap='jet', alpha=0.7)

    for i, temp in enumerate(isotherm_levels_detailed):
        contour = ax1.contour(x*1000, y*1000, T_max, levels=[temp],
                             colors=[isotherm_colors[i]], linewidths=[isotherm_widths[i]],
                             linestyles=[isotherm_styles[i]])
        ax1.clabel(contour, inline=True, fontsize=7, fmt=f'{int(temp)}K')

    ax1.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2.5, alpha=0.7)
    ax1.set_xlabel('x (mm)', fontsize=11)
    ax1.set_ylabel('y (mm)', fontsize=11)
    ax1.set_title('Detailed Temperature Isotherms\n(Blue=Cool, Orange=HAZ, Red=Fusion)',
                  fontsize=12, fontweight='bold')
    plt.colorbar(im1, ax=ax1, label='Temperature (K)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '1_detailed_isotherms.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # PLOT 2: Isotherm-Only View
    print("Creating Plot 2: Isotherm-Only View...")
    fig2 = plt.figure(figsize=(10, 8))
    ax2 = fig2.add_subplot(111)
    ax2.set_facecolor('white')

    for i, temp in enumerate(isotherm_levels_detailed):
        contour = ax2.contour(x*1000, y*1000, T_max, levels=[temp],
                             colors=[isotherm_colors[i]], linewidths=[isotherm_widths[i]],
                             linestyles=[isotherm_styles[i]])
        ax2.clabel(contour, inline=True, fontsize=8, fmt=f'{int(temp)}K')

    ax2.contour(x*1000, y*1000, T_max, levels=[T_crit], colors='cyan', linewidths=3, linestyles='--')
    ax2.contour(x*1000, y*1000, T_max, levels=[T_melt], colors='white', linewidths=3.5, linestyles='-')
    ax2.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2.5)
    ax2.set_xlabel('x (mm)', fontsize=11)
    ax2.set_ylabel('y (mm)', fontsize=11)
    ax2.set_title('Isotherm-Only View\n(Cyan=HAZ boundary, White=Fusion boundary)',
                  fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.2)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '2_isotherm_only.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # PLOT 3: Color-Coded Isotherm Families
    print("Creating Plot 3: Color-Coded Isotherm Families...")
    fig3 = plt.figure(figsize=(10, 8))
    ax3 = fig3.add_subplot(111)
    ax3.contourf(x*1000, y*1000, T_max, levels=30, cmap='gray', alpha=0.3)

    cool_levels = isotherm_levels_detailed[isotherm_levels_detailed < T_crit]
    if len(cool_levels) > 0:
        ax3.contour(x*1000, y*1000, T_max, levels=cool_levels, colors='blue', linewidths=1.5, alpha=0.8)

    haz_levels = isotherm_levels_detailed[(isotherm_levels_detailed >= T_crit) &
                                          (isotherm_levels_detailed < T_melt)]
    if len(haz_levels) > 0:
        ax3.contour(x*1000, y*1000, T_max, levels=haz_levels, colors='orange', linewidths=2, alpha=0.9)

    fusion_levels = isotherm_levels_detailed[isotherm_levels_detailed >= T_melt]
    if len(fusion_levels) > 0:
        ax3.contour(x*1000, y*1000, T_max, levels=fusion_levels, colors='red', linewidths=2.5, alpha=1.0)

    ax3.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2.5)
    ax3.set_xlabel('x (mm)', fontsize=11)
    ax3.set_ylabel('y (mm)', fontsize=11)
    ax3.set_title('Color-Coded Isotherm Families\n(Blue=Cool, Orange=HAZ, Red=Fusion)',
                  fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '3_color_coded_isotherms.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # PLOT 4: Temperature Gradient Magnitude
    print("Creating Plot 4: Temperature Gradient Magnitude...")
    fig4 = plt.figure(figsize=(10, 8))
    ax4 = fig4.add_subplot(111)
    dTdx, dTdy = np.gradient(T_max)
    grad_magnitude = np.sqrt((dTdx/dx)**2 + (dTdy/dy)**2)
    im4 = ax4.contourf(x*1000, y*1000, grad_magnitude, levels=40, cmap='plasma')
    contour_levels = np.linspace(grad_magnitude.min(), grad_magnitude.max(), 10)
    ax4.contour(x*1000, y*1000, grad_magnitude, levels=contour_levels, colors='white', linewidths=0.5)
    ax4.contour(x*1000, y*1000, T_max, levels=[T_crit, T_melt], colors=['cyan', 'white'], linewidths=2)
    ax4.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2)
    ax4.set_xlabel('x (mm)', fontsize=11)
    ax4.set_ylabel('y (mm)', fontsize=11)
    ax4.set_title('Temperature Gradient Magnitude\n(Shows heat flow patterns)',
                  fontsize=12, fontweight='bold')
    plt.colorbar(im4, ax=ax4, label='|∇T| (K/m)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '4_temperature_gradient.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # PLOT 5: Fusion Zone & HAZ Regions
    print("Creating Plot 5: Fusion Zone & HAZ Regions...")
    fig5 = plt.figure(figsize=(10, 8))
    ax5 = fig5.add_subplot(111)
    if fusion_zone.any():
        ax5.contourf(x*1000, y*1000, fusion_zone.astype(float), levels=[0.5, 1.5],
                     colors=['red'], alpha=0.4)
    if HAZ_zone.any():
        ax5.contourf(x*1000, y*1000, HAZ_zone.astype(float), levels=[0.5, 1.5],
                     colors=['orange'], alpha=0.3)

    for temp in [T_crit, T_melt]:
        ax5.contour(x*1000, y*1000, T_max, levels=[temp], colors='black', linewidths=2.5)

    ax5.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2.5)
    ax5.set_xlabel('x (mm)', fontsize=11)
    ax5.set_ylabel('y (mm)', fontsize=11)
    ax5.set_title('Fusion Zone & HAZ Regions\n(with boundary isotherms)',
                  fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '5_fusion_haz_zones.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # PLOT 6: Centerline Temperature
    print("Creating Plot 6: Centerline Temperature...")
    fig6 = plt.figure(figsize=(10, 8))
    ax6 = fig6.add_subplot(111)
    ax6.plot(x*1000, T_max[ny // 2, :], 'r-', linewidth=2.5, label='Peak T')
    ax6.plot(x*1000, T_final[ny // 2, :], 'b-', linewidth=2.5, label='Final T')

    for temp in isotherm_levels_detailed[::2]:
        ax6.axhline(temp, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
        ax6.text(x[-1]*1000*0.98, temp, f'{int(temp)}K', fontsize=7, ha='right', va='center')

    ax6.axhline(T_melt, color='red', linestyle='--', linewidth=2, alpha=0.7, label='T_melt')
    ax6.axhline(T_crit, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='T_HAZ')
    ax6.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2)
    ax6.set_xlabel('x (mm)', fontsize=11)
    ax6.set_ylabel('Temperature (K)', fontsize=11)
    ax6.set_title('Centerline Temperature\n(with isotherm levels)', fontsize=12, fontweight='bold')
    ax6.legend(fontsize=9, loc='upper right')
    ax6.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '6_centerline_temperature.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # PLOT 7: Transverse Temperature Profile
    print("Creating Plot 7: Transverse Temperature Profile...")
    fig7 = plt.figure(figsize=(10, 8))
    ax7 = fig7.add_subplot(111)
    ix_center = int(nx * 0.5)
    T_transverse = T_max[:, ix_center]
    ax7.plot(y*1000, T_transverse, 'r-', linewidth=2.5)

    for temp in isotherm_levels_detailed:
        if T_transverse.max() > temp:
            ax7.axhline(temp, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
            ax7.text(y[-1]*1000*0.98, temp, f'{int(temp)}K', fontsize=7, ha='right', va='center')

    ax7.axhline(T_melt, color='red', linestyle='--', linewidth=2)
    ax7.axhline(T_crit, color='orange', linestyle='--', linewidth=2)
    ax7.set_xlabel('y (mm)', fontsize=11)
    ax7.set_ylabel('Peak Temperature (K)', fontsize=11)
    ax7.set_title('Transverse Temperature Profile\nat Weld Center', fontsize=12, fontweight='bold')
    ax7.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '7_transverse_temperature.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # PLOT 8: Weld Width Along Length
    print("Creating Plot 8: Weld Width Along Length...")
    fig8 = plt.figure(figsize=(10, 8))
    ax8 = fig8.add_subplot(111)
    if fusion_zone.any():
        weld_widths = []
        x_weld_pos = []
        iy_center = ny // 2

        for i in range(nx):
            if fusion_zone[:, i].any():
                y_idx = np.where(fusion_zone[:, i])[0]
                if len(y_idx) > 1:
                    width = (y[y_idx[-1]] - y[y_idx[0]]) * 1000
                    weld_widths.append(width)
                    x_weld_pos.append(x[i] * 1000)

        if weld_widths:
            ax8.plot(x_weld_pos, weld_widths, 'b-o', linewidth=2, markersize=4, label='Weld Width')
            ax8.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2.5, label='Interface')
            ax8.axhline(np.mean(weld_widths), color='red', linestyle='--', linewidth=2,
                       label=f'Avg: {np.mean(weld_widths):.2f}mm')
            ax8.set_xlabel('x (mm)', fontsize=11)
            ax8.set_ylabel('Width (mm)', fontsize=11)
            ax8.set_title('Weld Width Along Length', fontsize=12, fontweight='bold')
            ax8.legend(fontsize=9)
            ax8.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '8_weld_width.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # PLOT 9: Temperature in Celsius with Isotherms
    print("Creating Plot 9: Temperature (°C) with Isotherms...")
    fig9 = plt.figure(figsize=(10, 8))
    ax9 = fig9.add_subplot(111)
    T_celsius = T_max - 273.15
    im9 = ax9.contourf(x*1000, y*1000, T_celsius, levels=40, cmap='hot')
    isotherm_celsius = [(temp - 273.15) for temp in [T_crit, T_melt]]
    ax9.contour(x*1000, y*1000, T_celsius, levels=isotherm_celsius,
                colors=['cyan', 'white'], linewidths=[2.5, 3])
    ax9.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2)
    ax9.set_xlabel('x (mm)', fontsize=11)
    ax9.set_ylabel('y (mm)', fontsize=11)
    ax9.set_title('Temperature (°C) with Isotherms', fontsize=12, fontweight='bold')
    plt.colorbar(im9, ax=ax9, label='Temperature (°C)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '9_temperature_celsius.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # PLOT 10: 3D Peak Temperature
    print("Creating Plot 10: 3D Peak Temperature...")
    fig10 = plt.figure(figsize=(12, 10))
    ax10 = fig10.add_subplot(111, projection='3d')
    surf1 = ax10.plot_surface(X*1000, Y*1000, T_max, cmap='hot', edgecolor='none', alpha=0.8)
    ax10.set_xlabel('x (mm)', fontsize=10)
    ax10.set_ylabel('y (mm)', fontsize=10)
    ax10.set_zlabel('Temperature (K)', fontsize=10)
    ax10.set_title('3D Peak Temperature', fontsize=12, fontweight='bold')
    fig10.colorbar(surf1, ax=ax10, shrink=0.5, label='T (K)')
    ax10.view_init(elev=25, azim=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '10_3d_peak_temperature.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # PLOT 11: 3D with Isotherm Projections
    print("Creating Plot 11: 3D with Isotherm Projections...")
    fig11 = plt.figure(figsize=(12, 10))
    ax11 = fig11.add_subplot(111, projection='3d')
    surf2 = ax11.plot_surface(X*1000, Y*1000, T_max, cmap='jet', edgecolor='none', alpha=0.7)
    ax11.contour(X*1000, Y*1000, T_max, levels=isotherm_levels_detailed,
                zdir='z', offset=T0, cmap='coolwarm', linewidths=1.5)
    ax11.set_xlabel('x (mm)', fontsize=10)
    ax11.set_ylabel('y (mm)', fontsize=10)
    ax11.set_zlabel('Temperature (K)', fontsize=10)
    ax11.set_title('3D with Isotherm Projections', fontsize=12, fontweight='bold')
    fig11.colorbar(surf2, ax=ax11, shrink=0.5, label='T (K)')
    ax11.view_init(elev=30, azim=135)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '11_3d_isotherm_projections.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # PLOT 12: 3D Zones Scatter
    print("Creating Plot 12: 3D Zones Scatter...")
    fig12 = plt.figure(figsize=(12, 10))
    ax12 = fig12.add_subplot(111, projection='3d')

    if fusion_zone.any():
        x_fusion = X[fusion_zone] * 1000
        y_fusion = Y[fusion_zone] * 1000
        t_fusion = T_max[fusion_zone]
        ax12.scatter(x_fusion[::2], y_fusion[::2], t_fusion[::2], c='red', marker='s',
                    s=3, alpha=0.8, label='Fusion')

    if HAZ_zone.any():
        x_haz = X[HAZ_zone] * 1000
        y_haz = Y[HAZ_zone] * 1000
        t_haz = T_max[HAZ_zone]
        ax12.scatter(x_haz[::3], y_haz[::3], t_haz[::3], c='orange', marker='.',
                    s=1, alpha=0.6, label='HAZ')

    ax12.set_xlabel('x (mm)', fontsize=10)
    ax12.set_ylabel('y (mm)', fontsize=10)
    ax12.set_zlabel('Temperature (K)', fontsize=10)
    ax12.set_title('3D Zones Scatter', fontsize=12, fontweight='bold')
    ax12.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '12_3d_zones_scatter.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # PLOT 13: 3D Temperature Gradient
    print("Creating Plot 13: 3D Temperature Gradient...")
    fig13 = plt.figure(figsize=(12, 10))
    ax13 = fig13.add_subplot(111, projection='3d')
    grad_magnitude = np.sqrt((np.gradient(T_max)[0]/dx)**2 + (np.gradient(T_max)[1]/dy)**2)
    surf4 = ax13.plot_surface(X*1000, Y*1000, grad_magnitude, cmap='plasma',
                              edgecolor='none', alpha=0.9)
    ax13.set_xlabel('x (mm)', fontsize=10)
    ax13.set_ylabel('y (mm)', fontsize=10)
    ax13.set_zlabel('|∇T| (K/m)', fontsize=10)
    ax13.set_title('3D Temperature Gradient', fontsize=12, fontweight='bold')
    fig13.colorbar(surf4, ax=ax13, shrink=0.5, label='|∇T| (K/m)')
    ax13.view_init(elev=20, azim=60)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '13_3d_temperature_gradient.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # PLOT 14-17: Thermal Cycles (if history available)
    if df_history is not None:
        time_history = df_history['time'].values
        T_history = [df_history[f'T_pt{i+1}'].values for i in range(3)
                     if f'T_pt{i+1}' in df_history.columns]

        # PLOT 14: Thermal Cycles
        print("Creating Plot 14: Thermal Cycles...")
        fig14 = plt.figure(figsize=(10, 8))
        ax14 = fig14.add_subplot(111)
        colors_tc = ['blue', 'red', 'green']

        for i, T_hist in enumerate(T_history):
            ax14.plot(time_history, T_hist, color=colors_tc[i], linewidth=2,
                     label=f'Point {i+1}')

        for temp in [T_crit, T_melt]:
            ax14.axhline(temp, linestyle='--', linewidth=2, alpha=0.6)

        ax14.set_xlabel('Time (s)', fontsize=11)
        ax14.set_ylabel('Temperature (K)', fontsize=11)
        ax14.set_title('Thermal Cycles', fontsize=12, fontweight='bold')
        ax14.legend(fontsize=9)
        ax14.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '14_thermal_cycles.png'), dpi=300, bbox_inches='tight')
        plt.close()

        # PLOT 15: Cooling Rates
        print("Creating Plot 15: Cooling Rates...")
        fig15 = plt.figure(figsize=(10, 8))
        ax15 = fig15.add_subplot(111)

        for i, T_hist in enumerate(T_history):
            if len(T_hist) > 10:
                cooling_rate = np.gradient(T_hist, time_history)
                ax15.plot(time_history, cooling_rate, color=colors_tc[i], linewidth=2,
                         label=f'Point {i+1}')

        ax15.axhline(0, color='black', linestyle='-', linewidth=0.5)
        ax15.set_xlabel('Time (s)', fontsize=11)
        ax15.set_ylabel('Cooling Rate (K/s)', fontsize=11)
        ax15.set_title('Cooling Rates', fontsize=12, fontweight='bold')
        ax15.legend(fontsize=9)
        ax15.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '15_cooling_rates.png'), dpi=300, bbox_inches='tight')
        plt.close()

        # PLOT 16: Final Temperature with Monitor Points
        print("Creating Plot 16: Final Temperature...")
        fig16 = plt.figure(figsize=(10, 8))
        ax16 = fig16.add_subplot(111)
        im_final = ax16.contourf(x*1000, y*1000, T_final, levels=40, cmap='jet')
        ax16.contour(x*1000, y*1000, T_final, levels=[T_crit, T_melt],
                     colors=['cyan', 'white'], linewidths=2)
        ax16.axvline(midpoint*1000, color='yellow', linestyle='--', linewidth=2)

        # Mark monitoring points
        monitor_pts = [(int(nx*0.35), ny//2), (nx//2, ny//2), (int(nx*0.65), ny//2)]
        for i, (ix, iy) in enumerate(monitor_pts):
            ax16.plot(x[ix]*1000, y[iy]*1000, 'wo', markersize=8,
                     markeredgecolor='black', markeredgewidth=2)
            ax16.text(x[ix]*1000, y[iy]*1000 + 5, f'{i+1}', ha='center', va='bottom',
                     color='white', fontweight='bold', fontsize=10)

        ax16.set_xlabel('x (mm)', fontsize=11)
        ax16.set_ylabel('y (mm)', fontsize=11)
        ax16.set_title('Final Temperature', fontsize=12, fontweight='bold')
        plt.colorbar(im_final, ax=ax16, label='T (K)')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '16_final_temperature.png'), dpi=300, bbox_inches='tight')
        plt.close()

        # PLOT 17: Peak T vs Position
        print("Creating Plot 17: Peak T vs Position...")
        fig17 = plt.figure(figsize=(10, 8))
        ax17 = fig17.add_subplot(111)
        peak_centerline = T_max[ny // 2, :]
        ax17.plot(x*1000, peak_centerline, 'r-', linewidth=2.5, label='Peak T')
        ax17.fill_between(x*1000, T0, peak_centerline, where=(peak_centerline >= T_melt),
                          color='red', alpha=0.3, label='Fusion Zone')
        ax17.fill_between(x*1000, T0, peak_centerline,
                          where=((peak_centerline >= T_crit) & (peak_centerline < T_melt)),
                          color='orange', alpha=0.3, label='HAZ')
        ax17.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2.5)
        ax17.set_xlabel('x (mm)', fontsize=11)
        ax17.set_ylabel('Peak Temperature (K)', fontsize=11)
        ax17.set_title('Peak T vs Position', fontsize=12, fontweight='bold')
        ax17.legend(fontsize=9)
        ax17.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '17_peak_temperature_vs_position.png'),
                    dpi=300, bbox_inches='tight')
        plt.close()

def main():
    """Main visualization function."""
    print("="*60)
    print("Complete Welding Simulation Visualization")
    print("Generating all 17 plots from Python implementation")
    print("="*60)
    print()

    print("Loading simulation results...")
    df = load_results()
    df_history = load_thermal_history()

    print("Preparing data...")
    x, y, X, Y, T_final, T_max, nx, ny = prepare_data(df)

    print("\nGenerating plots...")
    save_all_plots(x, y, X, Y, T_final, T_max, df_history, nx, ny)

    print("\n" + "="*60)
    print("Visualization complete!")
    print("All 17 plots saved in output/ directory:")
    print("  1. Detailed Temperature Isotherms")
    print("  2. Isotherm-Only View")
    print("  3. Color-Coded Isotherm Families")
    print("  4. Temperature Gradient Magnitude")
    print("  5. Fusion Zone & HAZ Regions")
    print("  6. Centerline Temperature")
    print("  7. Transverse Temperature Profile")
    print("  8. Weld Width Along Length")
    print("  9. Temperature (°C) with Isotherms")
    print(" 10. 3D Peak Temperature")
    print(" 11. 3D with Isotherm Projections")
    print(" 12. 3D Zones Scatter")
    print(" 13. 3D Temperature Gradient")
    print(" 14. Thermal Cycles")
    print(" 15. Cooling Rates")
    print(" 16. Final Temperature")
    print(" 17. Peak T vs Position")
    print("="*60)

if __name__ == '__main__':
    main()
