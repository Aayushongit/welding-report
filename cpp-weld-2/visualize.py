#!/usr/bin/env python3
"""
Visualization script for C++ welding simulation results.
Reads CSV output files and creates plots.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
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

def plot_temperature_field(df, output_dir='output/plots'):
    """Plot 2D temperature field."""
    os.makedirs(output_dir, exist_ok=True)

    # Get grid dimensions
    nx = df['i'].max() + 1
    ny = df['j'].max() + 1

    # Reshape data
    x = df['x'].values.reshape(ny, nx)[0, :] * 1000  # Convert to mm
    y = df['y'].values.reshape(ny, nx)[:, 0] * 1000  # Convert to mm
    T_final = df['T_final'].values.reshape(ny, nx)
    T_max = df['T_max'].values.reshape(ny, nx)

    # Plot peak temperature
    fig, ax = plt.subplots(figsize=(12, 6))
    contour = ax.contourf(x, y, T_max, levels=50, cmap='hot')
    plt.colorbar(contour, ax=ax, label='Temperature (K)')

    # Add isotherms
    T_crit = 1273.0  # HAZ boundary
    T_melt = 1767.0  # Fusion boundary
    ax.contour(x, y, T_max, levels=[T_crit, T_melt],
               colors=['cyan', 'white'], linewidths=2, linestyles=['--', '-'])

    ax.set_xlabel('x (mm)', fontsize=12)
    ax.set_ylabel('y (mm)', fontsize=12)
    ax.set_title('Peak Temperature Distribution', fontsize=14, fontweight='bold')
    ax.axvline(x[len(x)//2], color='yellow', linestyle=':', linewidth=2, alpha=0.7, label='Interface')
    ax.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'peak_temperature.png'), dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir}/peak_temperature.png")

    # Plot final temperature
    fig, ax = plt.subplots(figsize=(12, 6))
    contour = ax.contourf(x, y, T_final, levels=50, cmap='jet')
    plt.colorbar(contour, ax=ax, label='Temperature (K)')
    ax.set_xlabel('x (mm)', fontsize=12)
    ax.set_ylabel('y (mm)', fontsize=12)
    ax.set_title('Final Temperature Distribution', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'final_temperature.png'), dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir}/final_temperature.png")

    # Plot centerline temperature
    fig, ax = plt.subplots(figsize=(10, 6))
    centerline_idx = ny // 2
    ax.plot(x, T_max[centerline_idx, :], 'r-', linewidth=2.5, label='Peak Temperature')
    ax.plot(x, T_final[centerline_idx, :], 'b-', linewidth=2.5, label='Final Temperature')
    ax.axhline(T_melt, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Melting Point')
    ax.axhline(T_crit, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='HAZ Boundary')
    ax.axvline(x[len(x)//2], color='yellow', linestyle=':', linewidth=2)

    ax.set_xlabel('x (mm)', fontsize=12)
    ax.set_ylabel('Temperature (K)', fontsize=12)
    ax.set_title('Centerline Temperature Profile', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'centerline_temperature.png'), dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir}/centerline_temperature.png")

    return x, y, T_max, T_final

def plot_thermal_history(df_history, output_dir='output/plots'):
    """Plot thermal cycles."""
    if df_history is None:
        return

    os.makedirs(output_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    time = df_history['time'].values
    colors = ['blue', 'red', 'green']

    for i, col in enumerate(['T_pt1', 'T_pt2', 'T_pt3']):
        if col in df_history.columns:
            ax.plot(time, df_history[col].values, color=colors[i],
                   linewidth=2, label=f'Point {i+1}')

    # Add reference lines
    T_crit = 1273.0
    T_melt = 1767.0
    ax.axhline(T_melt, color='red', linestyle='--', linewidth=2, alpha=0.6, label='Melting Point')
    ax.axhline(T_crit, color='orange', linestyle='--', linewidth=2, alpha=0.6, label='HAZ Boundary')

    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Temperature (K)', fontsize=12)
    ax.set_title('Thermal Cycles at Monitoring Points', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'thermal_cycles.png'), dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir}/thermal_cycles.png")

def plot_3d_surface(x, y, T_max, output_dir='output/plots'):
    """Create 3D surface plot."""
    from mpl_toolkits.mplot3d import Axes3D

    os.makedirs(output_dir, exist_ok=True)

    X, Y = np.meshgrid(x, y)

    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')

    surf = ax.plot_surface(X, Y, T_max, cmap='hot', edgecolor='none', alpha=0.8)
    ax.set_xlabel('x (mm)', fontsize=10)
    ax.set_ylabel('y (mm)', fontsize=10)
    ax.set_zlabel('Temperature (K)', fontsize=10)
    ax.set_title('3D Peak Temperature Surface', fontsize=12, fontweight='bold')
    fig.colorbar(surf, ax=ax, shrink=0.5, label='T (K)')
    ax.view_init(elev=25, azim=45)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '3d_temperature.png'), dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir}/3d_temperature.png")

def plot_zones(x, y, T_max, output_dir='output/plots'):
    """Plot fusion and HAZ zones."""
    os.makedirs(output_dir, exist_ok=True)

    T_crit = 1273.0
    T_melt = 1767.0

    fusion_zone = T_max >= T_melt
    HAZ_zone = (T_max >= T_crit) & (T_max < T_melt)

    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot zones
    if fusion_zone.any():
        ax.contourf(x, y, fusion_zone.astype(float), levels=[0.5, 1.5],
                    colors=['red'], alpha=0.4, label='Fusion Zone')
    if HAZ_zone.any():
        ax.contourf(x, y, HAZ_zone.astype(float), levels=[0.5, 1.5],
                    colors=['orange'], alpha=0.3, label='HAZ')

    # Plot boundaries
    ax.contour(x, y, T_max, levels=[T_crit, T_melt],
              colors=['orange', 'red'], linewidths=2.5, linestyles=['--', '-'])

    ax.axvline(x[len(x)//2], color='yellow', linestyle=':', linewidth=2.5)
    ax.set_xlabel('x (mm)', fontsize=12)
    ax.set_ylabel('y (mm)', fontsize=12)
    ax.set_title('Fusion Zone and HAZ Regions', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'zones.png'), dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir}/zones.png")

def main():
    """Main visualization function."""
    print("Loading simulation results...")
    df = load_results()
    df_history = load_thermal_history()

    print("Creating plots...")
    x, y, T_max, T_final = plot_temperature_field(df)
    plot_thermal_history(df_history)
    plot_3d_surface(x, y, T_max)
    plot_zones(x, y, T_max)

    print("\nVisualization complete!")
    print("All plots saved in output/plots/ directory")

    # Show plots
    plt.show()

if __name__ == '__main__':
    main()
