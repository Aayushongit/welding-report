#!/usr/bin/env python3
"""
Create MP4 video from TIG welding simulation frames
Shows temperature contours with HAZ and fusion zone boundaries
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import cm
import glob
import os

def read_config(filename='output_cpp/weld_config.txt'):
    """Read configuration"""
    config = {}
    with open(filename, 'r') as f:
        for line in f:
            key, value = line.strip().split('=')
            config[key] = float(value)
    return config

def read_frame(filename):
    """Read a single frame"""
    return np.loadtxt(filename, delimiter=',')

def create_video():
    """Create animated video with temperature contours"""
    print("Creating TIG welding simulation video...")

    # Read configuration
    config = read_config()
    nx = int(config['nx'])
    ny = int(config['ny'])
    Lx = config['Lx']
    Ly = config['Ly']
    T_melt = (config['T_melt_1'] + config['T_melt_2']) / 2.0
    T_crit = (config['T_crit_1'] + config['T_crit_2']) / 2.0
    T0 = config['T0']
    midpoint = config['midpoint']

    # Get all frame files
    frame_files = sorted(glob.glob('output_cpp/frames/frame_*.csv'))

    if not frame_files:
        print("Error: No frame files found in output_cpp/frames/")
        print("Make sure the simulation has run successfully.")
        return

    print(f"Found {len(frame_files)} frames")

    # Create mesh grid
    x = np.linspace(0, Lx, nx)
    y = np.linspace(-Ly/2, Ly/2, ny)
    X, Y = np.meshgrid(x, y)

    # Setup figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    def update_frame(frame_num):
        """Update function for animation"""
        ax1.clear()
        ax2.clear()

        # Read temperature data
        T = read_frame(frame_files[frame_num])

        # Extract frame number from filename
        frame_name = os.path.basename(frame_files[frame_num])
        step = int(frame_name.split('_')[1].split('.')[0])
        t = step * 0.02  # dt = 0.02

        # ===== Top plot: Temperature contours with zones =====
        # Temperature contours
        levels = np.linspace(T0, T.max(), 30)
        contourf = ax1.contourf(X*1000, Y*1000, T, levels=levels, cmap='hot', extend='max')

        # Add critical isotherms
        if T.max() >= T_crit:
            cs_crit = ax1.contour(X*1000, Y*1000, T, levels=[T_crit],
                                 colors=['cyan'], linewidths=2.5, linestyles='--')
            ax1.clabel(cs_crit, inline=True, fontsize=9, fmt=f'{int(T_crit)} K (HAZ)')

        if T.max() >= T_melt:
            cs_melt = ax1.contour(X*1000, Y*1000, T, levels=[T_melt],
                                 colors=['white'], linewidths=3.0, linestyles='-')
            ax1.clabel(cs_melt, inline=True, fontsize=9, fmt=f'{int(T_melt)} K (Fusion)')

        # Material interface
        ax1.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2, alpha=0.7)

        # Arc position
        x_arc = 0.02 + 0.006 * t
        if x_arc <= Lx:
            ax1.plot(x_arc*1000, 0, 'r*', markersize=20, markeredgecolor='white',
                    markeredgewidth=1.5, label='TIG Arc')

        ax1.set_xlabel('x (mm)', fontsize=12)
        ax1.set_ylabel('y (mm)', fontsize=12)
        ax1.set_title(f'TIG Welding Temperature Distribution\n' +
                     f'Time: {t:.2f} s | Arc position: {x_arc*1000:.1f} mm | ' +
                     f'Max T: {T.max():.0f} K ({T.max()-273.15:.0f} °C)',
                     fontsize=13, fontweight='bold')
        ax1.grid(True, alpha=0.3)


        # Colorbar
        if frame_num == 0:
            global cbar
            cbar = plt.colorbar(contourf, ax=ax1, label='Temperature (K)')
        else:
            cbar.update_normal(contourf)

        # ===== Bottom plot: Centerline temperature =====
        centerline_idx = ny // 2
        T_centerline = T[centerline_idx, :]

        ax2.plot(x*1000, T_centerline, 'r-', linewidth=2.5, label='Temperature')
        ax2.axhline(T_melt, color='red', linestyle='--', linewidth=2, alpha=0.7,
                   label=f'Melting Point ({T_melt:.0f} K)')
        ax2.axhline(T_crit, color='orange', linestyle='--', linewidth=2, alpha=0.7,
                   label=f'HAZ Boundary ({T_crit:.0f} K)')
        ax2.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2,
                   label='Material Interface')

        # Shade fusion and HAZ zones
        ax2.fill_between(x*1000, T0, T_centerline, where=(T_centerline >= T_melt),
                        color='red', alpha=0.3, label='Fusion Zone')
        ax2.fill_between(x*1000, T0, T_centerline,
                        where=((T_centerline >= T_crit) & (T_centerline < T_melt)),
                        color='orange', alpha=0.3, label='HAZ')

        # Arc position marker
        if x_arc <= Lx:
            ax2.axvline(x_arc*1000, color='red', linestyle='-', linewidth=2, alpha=0.5)

        ax2.set_xlabel('x (mm)', fontsize=12)
        ax2.set_ylabel('Temperature (K)', fontsize=12)
        ax2.set_title('Centerline Temperature Profile', fontsize=12, fontweight='bold')
        ax2.legend(fontsize=9, loc='upper right', ncol=2)
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim([T0 - 50, T.max() * 1.1])

        plt.tight_layout()

        if frame_num % 10 == 0:
            print(f"Processing frame {frame_num + 1}/{len(frame_files)}")

    # Create animation
    print("Generating animation...")
    anim = animation.FuncAnimation(fig, update_frame, frames=len(frame_files),
                                   interval=100, repeat=True)

    # Save as MP4
    output_file = 'output_cpp/tig_welding_simulation.mp4'
    print(f"Saving video to {output_file}...")

    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=10, metadata=dict(artist='TIG Simulation'),
                   bitrate=3000)

    anim.save(output_file, writer=writer, dpi=150)

    print(f"\n{'='*60}")
    print(f"✓ Video created successfully!")
    print(f"  File: {output_file}")
    print(f"  Frames: {len(frame_files)}")
    print(f"  Duration: {len(frame_files)/10:.1f} seconds")
    print(f"  FPS: 10")
    print(f"{'='*60}\n")



if __name__ == "__main__":
    create_video()
