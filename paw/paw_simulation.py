import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import os
import time
from dataclasses import dataclass
import argparse
import json
from numba import njit
import seaborn as sns
import imageio.v2 as imageio
from io import BytesIO
from PIL import Image

@dataclass
class SimulationConfig:
    """Configuration for the welding simulation."""
    # Domain and mesh
    Lx: float = 0.15
    Ly: float = 0.10
    thickness: float = 0.006
    nx: int = 151
    ny: int = 101

    # Materials
    mat_1_name: str = "Mild Steel"
    mat_1_rho: float = 7850.0
    mat_1_cp: float = 500.0
    mat_1_k: float = 45.0
    mat_1_T_melt: float = 1811.0
    mat_1_T_crit: float = 1273.0

    mat_2_name: str = "Stainless Steel 304"
    mat_2_rho: float = 7900.0
    mat_2_cp: float = 500.0
    mat_2_k: float = 16.3
    mat_2_T_melt: float = 1723.0
    mat_2_T_crit: float = 1273.0

    # Heat source (Plasma Arc Welding)
    Q_paw: float = 2500.0   # Heat input in W
    R_paw: float = 0.002     # Arc radius in m
    H_paw: float = 0.005     # Arc length in m
    v_weld: float = 0.008
    weld_x_position: float = 0.075  # Fixed x-position for welding along y-axis (Lx/2)
    weld_start_y: float = -0.05   # Starting y-position for welding along y-axis (-Ly/2)

    # Simulation parameters
    T0: float = 293.0
    h_conv: float = 20.0
    dt: float = 0.02
    theta: float = 0.5

    # Welding process
    snapshot_time: float = -1.0  # Time in seconds to take a snapshot. -1 to disable.

class Material:
    def __init__(self, name, rho, cp, k, T_melt, T_crit):
        self.name = name
        self.rho = rho
        self.cp = cp
        self.k = k
        self.alpha = k / (rho * cp)
        self.T_melt = T_melt
        self.T_crit = T_crit

def paw_heat_source(X, Y, x_arc, y_arc, Q, R, H):
    """
    Calculates the volumetric heat source for Plasma Arc Welding (PAW).
    """
    r_sq = (X - x_arc)**2 + (Y - y_arc)**2
    Qvol = (3 * Q) / (np.pi * R**2 * H) * np.exp(-3 * r_sq / R**2)
    return Qvol

@njit
def get_k(T, k, T_crit, T_melt):
    """Returns the thermal conductivity of the material at a given temperature."""
    if T < T_crit:
        return k
    elif T < T_melt:
        return k * (1 + (T - T_crit) / (T_melt - T_crit) * 0.1)
    else:
        return k * 1.1

@njit
def get_cp(T, cp, T_crit, T_melt):
    """Returns the specific heat of the material at a given temperature."""
    if T < T_crit:
        return cp
    elif T < T_melt:
        return cp * (1 + (T - T_crit) / (T_melt - T_crit) * 0.2)
    else:
        return cp * 1.2

@njit
def get_rho(T, rho, T_crit, T_melt):
    """Returns the density of the material at a given temperature."""
    if T < T_crit:
        return rho
    elif T < T_melt:
        return rho * (1 - (T - T_crit) / (T_melt - T_crit) * 0.05)
    else:
        return rho * 0.95

def save_plots(T, T_max, x, y, X, Y, T_crit, T_melt, T0, midpoint, time_history, T_history, monitor_pts, mat_1, mat_2, fusion_zone, HAZ_zone, dx, dy, nx, ny, snapshot_name=""):
    sns.set_theme(style="whitegrid")
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    isotherm_levels_detailed = np.array([400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1273, 1400, 1500, 1600, 1767, 1900, 2000, 2100, 2200])
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

    fig1 = plt.figure(figsize=(8, 6), num='1. Plot 1')
    plt.clf()
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
    ax1.set_title('Detailed Temperature Isotherms\n(Blue=Cool, Orange=HAZ, Red=Fusion)', fontsize=12, fontweight='bold')
    cbar1 = plt.colorbar(im1, ax=ax1, label='Temperature (K)')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'1_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')
    fig2 = plt.figure(figsize=(8, 6), num='2. Plot 2')
    plt.clf()
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
    ax2.set_title('Isotherm-Only View\n(Cyan=HAZ boundary, White=Fusion boundary)', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.2)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'2_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')
    fig3 = plt.figure(figsize=(8, 6), num='3. Plot 3')
    plt.clf()
    ax3 = fig3.add_subplot(111)
    ax3.contourf(x*1000, y*1000, T_max, levels=30, cmap='gray', alpha=0.3)

    cool_levels = isotherm_levels_detailed[isotherm_levels_detailed < T_crit]
    if len(cool_levels) > 0:
        ax3.contour(x*1000, y*1000, T_max, levels=cool_levels, colors='blue', linewidths=1.5, alpha=0.8)

    haz_levels = isotherm_levels_detailed[(isotherm_levels_detailed >= T_crit) & (isotherm_levels_detailed < T_melt)]
    if len(haz_levels) > 0:
        ax3.contour(x*1000, y*1000, T_max, levels=haz_levels, colors='orange', linewidths=2, alpha=0.9)

    fusion_levels = isotherm_levels_detailed[isotherm_levels_detailed >= T_melt]
    if len(fusion_levels) > 0:
        ax3.contour(x*1000, y*1000, T_max, levels=fusion_levels, colors='red', linewidths=2.5, alpha=1.0)

    ax3.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2.5)
    ax3.set_xlabel('x (mm)', fontsize=11)
    ax3.set_ylabel('y (mm)', fontsize=11)
    ax3.set_title('Color-Coded Isotherm Families\n(Blue=Cool, Orange=HAZ, Red=Fusion)', fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'3_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')
    fig4 = plt.figure(figsize=(8, 6), num='4. Plot 4')
    plt.clf()
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
    ax4.set_title('Temperature Gradient Magnitude\n(Shows heat flow patterns)', fontsize=12, fontweight='bold')
    plt.colorbar(im4, ax=ax4, label='|∇T| (K/m)')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'4_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')
    fig5 = plt.figure(figsize=(8, 6), num='5. Plot 5')
    plt.clf()
    ax5 = fig5.add_subplot(111)
    if fusion_zone.any():
        fusion_filled = ax5.contourf(x*1000, y*1000, fusion_zone.astype(float), levels=[0.5, 1.5], colors=['red'], alpha=0.4)
    if HAZ_zone.any():
        haz_filled = ax5.contourf(x*1000, y*1000, HAZ_zone.astype(float), levels=[0.5, 1.5], colors=['orange'], alpha=0.3)

    for temp in [T_crit, T_melt]:
        ax5.contour(x*1000, y*1000, T_max, levels=[temp], colors='black', linewidths=2.5)

    ax5.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2.5)
    ax5.set_xlabel('x (mm)', fontsize=11)
    ax5.set_ylabel('y (mm)', fontsize=11)
    ax5.set_title('Fusion Zone & HAZ Regions\n(with boundary isotherms)', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'5_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')
    fig6 = plt.figure(figsize=(8, 6), num='6. Plot 6')
    plt.clf()
    ax6 = fig6.add_subplot(111)
    ax6.plot(x*1000, T_max[ny // 2, :], 'r-', linewidth=2.5, label='Peak T')
    ax6.plot(x*1000, T[ny // 2, :], 'b-', linewidth=2.5, label='Final T')

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
    plt.savefig(os.path.join(output_dir, f'6_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')
    fig7 = plt.figure(figsize=(8, 6), num='7. Plot 7')
    plt.clf()
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
    plt.savefig(os.path.join(output_dir, f'7_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')
    fig8 = plt.figure(figsize=(8, 6), num='8. Plot 8')
    plt.clf()
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
            ax8.axhline(np.mean(weld_widths), color='red', linestyle='--', linewidth=2, label=f'Avg: {np.mean(weld_widths):.2f}mm')
            ax8.set_xlabel('x (mm)', fontsize=11)
            ax8.set_ylabel('Width (mm)', fontsize=11)
            ax8.set_title('Weld Width Along Length', fontsize=12, fontweight='bold')
            ax8.legend(fontsize=9)
            ax8.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'8_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')
    fig9 = plt.figure(figsize=(8, 6), num='9. Plot 9')
    plt.clf()
    ax9 = fig9.add_subplot(111)
    T_celsius = T_max - 273.15
    im9 = ax9.contourf(x*1000, y*1000, T_celsius, levels=40, cmap='hot')
    isotherm_celsius = [(temp - 273.15) for temp in [T_crit, T_melt]]
    ax9.contour(x*1000, y*1000, T_celsius, levels=isotherm_celsius, colors=['cyan', 'white'], linewidths=[2.5, 3])
    ax9.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2)
    ax9.set_xlabel('x (mm)', fontsize=11)
    ax9.set_ylabel('y (mm)', fontsize=11)
    ax9.set_title('Temperature (°C) with Isotherms', fontsize=12, fontweight='bold')
    plt.colorbar(im9, ax=ax9, label='Temperature (°C)')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'9_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')
                # Plot 10
    fig10 = plt.figure(figsize=(8, 6), num='10. 3D Plot 1')
    plt.clf()
    ax1_3d = fig10.add_subplot(111, projection='3d')
    surf1 = ax1_3d.plot_surface(X*1000, Y*1000, T_max, cmap='hot', edgecolor='none', alpha=0.8)
    ax1_3d.set_xlabel('x (mm)', fontsize=10)
    ax1_3d.set_ylabel('y (mm)', fontsize=10)
    ax1_3d.set_zlabel('Temperature (K)', fontsize=10)
    ax1_3d.set_title('3D Peak Temperature', fontsize=12, fontweight='bold')
    fig10.colorbar(surf1, ax=ax1_3d, shrink=0.5, label='T (K)')
    ax1_3d.view_init(elev=25, azim=45)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'10_3d_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')
    # Plot 11
    fig11 = plt.figure(figsize=(8, 6), num='11. 3D Plot 2')
    plt.clf()
    ax2_3d = fig11.add_subplot(111, projection='3d')
    surf2 = ax2_3d.plot_surface(X*1000, Y*1000, T_max, cmap='jet', edgecolor='none', alpha=0.7)

    ax2_3d.contour(X*1000, Y*1000, T_max, levels=isotherm_levels_detailed,
                  zdir='z', offset=T0, cmap='coolwarm', linewidths=1.5)
    ax2_3d.set_xlabel('x (mm)', fontsize=10)
    ax2_3d.set_ylabel('y (mm)', fontsize=10)
    ax2_3d.set_zlabel('Temperature (K)', fontsize=10)
    ax2_3d.set_title('3D with Isotherm Projections', fontsize=12, fontweight='bold')
    fig11.colorbar(surf2, ax=ax2_3d, shrink=0.5, label='T (K)')
    ax2_3d.view_init(elev=30, azim=135)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'11_3d_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')
    # Plot 12
    fig12 = plt.figure(figsize=(8, 6), num='12. 3D Plot 3')
    plt.clf()
    ax3_3d = fig12.add_subplot(111, projection='3d')

    if fusion_zone.any():
        x_fusion = X[fusion_zone] * 1000
        y_fusion = Y[fusion_zone] * 1000
        t_fusion = T_max[fusion_zone]
        ax3_3d.scatter(x_fusion[::2], y_fusion[::2], t_fusion[::2], c='red', marker='s', s=3, alpha=0.8, label='Fusion')

    if HAZ_zone.any():
        x_haz = X[HAZ_zone] * 1000
        y_haz = Y[HAZ_zone] * 1000
        t_haz = T_max[HAZ_zone]
        ax3_3d.scatter(x_haz[::3], y_haz[::3], t_haz[::3], c='orange', marker='.', s=1, alpha=0.6, label='HAZ')

    ax3_3d.set_xlabel('x (mm)', fontsize=10)
    ax3_3d.set_ylabel('y (mm)', fontsize=10)
    ax3_3d.set_zlabel('Temperature (K)', fontsize=10)
    ax3_3d.set_title('3D Zones Scatter', fontsize=12, fontweight='bold')
    ax3_3d.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'12_3d_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')
    # Plot 13
    fig13 = plt.figure(figsize=(8, 6), num='13. 3D Plot 4')
    plt.clf()
    ax4_3d = fig13.add_subplot(111, projection='3d')
    grad_magnitude = np.sqrt((np.gradient(T_max)[0]/dx)**2 + (np.gradient(T_max)[1]/dy)**2)
    surf4 = ax4_3d.plot_surface(X*1000, Y*1000, grad_magnitude, cmap='plasma', edgecolor='none', alpha=0.9)
    ax4_3d.set_xlabel('x (mm)', fontsize=10)
    ax4_3d.set_ylabel('y (mm)', fontsize=10)
    ax4_3d.set_zlabel('|∇T| (K/m)', fontsize=10)
    ax4_3d.set_title('3D Temperature Gradient', fontsize=12, fontweight='bold')
    fig13.colorbar(surf4, ax=ax4_3d, shrink=0.5, label='|∇T| (K/m)')
    ax4_3d.view_init(elev=20, azim=60)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'13_3d_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')
                # Plot 14
    fig14 = plt.figure(figsize=(8, 6), num='14. Thermal Cycle 1')
    plt.clf()
    ax1_tc = fig14.add_subplot(111)
    colors_tc = ['blue', 'red', 'green']
    for i, (iy, ix) in enumerate(monitor_pts):
        mat_name = mat_1.name if x[ix] < midpoint else mat_2.name
        ax1_tc.plot(time_history, T_history[i], color=colors_tc[i], linewidth=2,
                   label=f'Pt{i+1}: ({x[ix]*1000:.1f},{y[iy]*1000:.1f})mm - {mat_name}')

    for temp in [T_crit, T_melt]:
        ax1_tc.axhline(temp, linestyle='--', linewidth=2, alpha=0.6)

    ax1_tc.set_xlabel('Time (s)', fontsize=11)
    ax1_tc.set_ylabel('Temperature (K)', fontsize=11)
    ax1_tc.set_title('Thermal Cycles', fontsize=12, fontweight='bold')
    ax1_tc.legend(fontsize=9)
    ax1_tc.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'14_thermal_cycle{snapshot_name}.png'), dpi=300, bbox_inches='tight')
    # Plot 15
    fig15 = plt.figure(figsize=(8, 6), num='15. Thermal Cycle 2')
    plt.clf()
    ax2_tc = fig15.add_subplot(111)
    for i, (iy, ix) in enumerate(monitor_pts):
        T_hist = np.array(T_history[i])
        if len(T_hist) > 10:
            cooling_rate = np.gradient(T_hist, time_history)
            mat_name = mat_1.name if x[ix] < midpoint else mat_2.name
            ax2_tc.plot(time_history, cooling_rate, color=colors_tc[i], linewidth=2,
                       label=f'Pt{i+1} - {mat_name}')

    ax2_tc.axhline(0, color='black', linestyle='-', linewidth=0.5)
    ax2_tc.set_xlabel('Time (s)', fontsize=11)
    ax2_tc.set_ylabel('Cooling Rate (K/s)', fontsize=11)
    ax2_tc.set_title('Cooling Rates', fontsize=12, fontweight='bold')
    ax2_tc.legend(fontsize=9)
    ax2_tc.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'15_thermal_cycle{snapshot_name}.png'), dpi=300, bbox_inches='tight')
    # Plot 16
    fig16 = plt.figure(figsize=(8, 6), num='16. Thermal Cycle 3')
    plt.clf()
    ax3_tc = fig16.add_subplot(111)
    im_final = ax3_tc.contourf(x*1000, y*1000, T, levels=40, cmap='jet')
    ax3_tc.contour(x*1000, y*1000, T, levels=[T_crit, T_melt], colors=['cyan', 'white'], linewidths=2)
    ax3_tc.axvline(midpoint*1000, color='yellow', linestyle='--', linewidth=2)

    for i, (iy, ix) in enumerate(monitor_pts):
        ax3_tc.plot(x[ix]*1000, y[iy]*1000, 'wo', markersize=8, markeredgecolor='black', markeredgewidth=2)
        ax3_tc.text(x[ix]*1000, y[iy]*1000 + 5, f'{i+1}', ha='center', va='bottom',
                   color='white', fontweight='bold', fontsize=10)

    ax3_tc.set_xlabel('x (mm)', fontsize=11)
    ax3_tc.set_ylabel('y (mm)', fontsize=11)
    ax3_tc.set_title('Final Temperature', fontsize=12, fontweight='bold')
    plt.colorbar(im_final, ax=ax3_tc, label='T (K)')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'16_thermal_cycle{snapshot_name}.png'), dpi=300, bbox_inches='tight')
    # Plot 17
    fig17 = plt.figure(figsize=(8, 6), num='17. Thermal Cycle 4')
    plt.clf()
    ax4_tc = fig17.add_subplot(111)
    peak_centerline = T_max[ny // 2, :]
    ax4_tc.plot(x*1000, peak_centerline, 'r-', linewidth=2.5, label='Peak T')
    ax4_tc.fill_between(x*1000, T0, peak_centerline, where=(peak_centerline >= T_melt),
                        color='red', alpha=0.3, label='Fusion Zone')
    ax4_tc.fill_between(x*1000, T0, peak_centerline,
                        where=((peak_centerline >= T_crit) & (peak_centerline < T_melt)),
                        color='orange', alpha=0.3, label='HAZ')
    ax4_tc.axvline(midpoint*1000, color='yellow', linestyle=':', linewidth=2.5)
    ax4_tc.set_xlabel('x (mm)', fontsize=11)
    ax4_tc.set_ylabel('Peak Temperature (K)', fontsize=11)
    ax4_tc.set_title('Peak T vs Position', fontsize=12, fontweight='bold')
    ax4_tc.legend(fontsize=9)
    ax4_tc.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'17_thermal_cycle{snapshot_name}.png'), dpi=300, bbox_inches='tight')
    print(f"All plots saved in {output_dir}/ directory")
    plt.show()

def run_simulation(config: SimulationConfig):
    """Runs the welding simulation with the given configuration."""
    # Unpack config for easier access
    Lx, Ly, thickness, nx, ny = config.Lx, config.Ly, config.thickness, config.nx, config.ny
    Q_paw, R_paw, H_paw, v_weld, weld_x_position, weld_start_y = config.Q_paw, config.R_paw, config.H_paw, config.v_weld, config.weld_x_position, config.weld_start_y
    T0, h_conv, dt, theta = config.T0, config.h_conv, config.dt, config.theta
    snapshot_time = config.snapshot_time

    mat_1 = Material(config.mat_1_name, config.mat_1_rho, config.mat_1_cp, config.mat_1_k, config.mat_1_T_melt, config.mat_1_T_crit)
    mat_2 = Material(config.mat_2_name, config.mat_2_rho, config.mat_2_cp, config.mat_2_k, config.mat_2_T_melt, config.mat_2_T_crit)

    x = np.linspace(0, Lx, nx)
    y = np.linspace(-Ly/2, Ly/2, ny)
    X, Y = np.meshgrid(x, y)

    dx = x[1] - x[0]
    dy = y[1] - y[0]
    N = nx * ny

    midpoint = Lx / 2 # This remains Lx/2 as it defines the material interface

    T_melt = (mat_1.T_melt + mat_2.T_melt) / 2
    T_crit = (mat_1.T_crit + mat_2.T_crit) / 2

    def idx(i, j):
        return j * nx + i

    print("Simulating Plasma Arc Welding (PAW).")

    if snapshot_time > 0:
        t_end = snapshot_time
    else:
        t_end = (Ly/2 - weld_start_y) / v_weld + 10.0 # Adjusted for welding along y-axis
    nt = int(np.ceil(t_end / dt))

    print(f"Grid: {nx}x{ny}, Time steps: {nt}")
    print(f"Materials: {mat_1.name} | {mat_2.name}")
    print(f"Power: {Q_paw:.0f}W, Speed: {v_weld*1000:.1f}mm/s")

    ex = np.ones(nx)
    ey = np.ones(ny)
    Tx = sp.diags([ex, -2*ex, ex], [-1, 0, 1], shape=(nx, nx)) / dx**2
    Ty = sp.diags([ey, -2*ey, ey], [-1, 0, 1], shape=(ny, ny)) / dy**2
    Ix = sp.eye(nx, format='csc')
    Iy = sp.eye(ny, format='csc')

    L = sp.kron(Iy, Tx, format='csc') + sp.kron(Ty, Ix, format='csc')

    fixed = np.zeros(N, dtype=bool)
    fixed_indices = []

    for j in range(ny):
        for i in range(nx):
            if i == 0 or i == nx-1 or j == 0 or j == ny-1:
                ind = idx(i, j)
                fixed[ind] = True
                fixed_indices.append(ind)

    fixed_indices = np.array(fixed_indices, dtype=int)
    free_indices = np.where(~fixed)[0]

    T = np.full((ny, nx), T0)
    T_max = T.copy()

    monitor_pts = [
        (int(ny*0.5), int(nx*0.35)),
        (int(ny*0.5), int(nx*0.5)),
        (int(ny*0.5), int(nx*0.65)),
    ]
    T_history = {i: [] for i in range(len(monitor_pts))}
    time_history = []

    t = 0.0
    start_time = time.time()
    snapshot_taken = False
    frames = []
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    video_filename = os.path.join(output_dir, "paw_simulation.mp4")
    fig_video = plt.figure(figsize=(10, 6))

    for step in range(1, nt + 1):
        t += dt
        time_history.append(t)

        current_y_arc = weld_start_y + v_weld * t
        x_arc_fixed = weld_x_position

        if current_y_arc <= Ly/2: # Check if the arc is within the y-domain
            Qvol = paw_heat_source(X, Y, x_arc_fixed, current_y_arc, Q_paw, R_paw, H_paw)
        else:
            Qvol = np.zeros_like(X)

        k_vec = np.vectorize(get_k)
        cp_vec = np.vectorize(get_cp)
        rho_vec = np.vectorize(get_rho)

        k = np.where(X < midpoint, k_vec(T, mat_1.k, mat_1.T_crit, mat_1.T_melt), k_vec(T, mat_2.k, mat_2.T_crit, mat_2.T_melt))
        cp = np.where(X < midpoint, cp_vec(T, mat_1.cp, mat_1.T_crit, mat_1.T_melt), cp_vec(T, mat_2.cp, mat_2.T_crit, mat_2.T_melt))
        rho = np.where(X < midpoint, rho_vec(T, mat_1.rho, mat_1.T_crit, mat_1.T_melt), rho_vec(T, mat_2.rho, mat_2.T_crit, mat_2.T_melt))
        alpha = k / (rho * cp)

        I_mat = sp.eye(N, format='csc')
        A_full = (I_mat - theta * dt * sp.diags(alpha.ravel()) * L).tolil()
        B_full = (I_mat + (1 - theta) * dt * sp.diags(alpha.ravel()) * L).tolil()

        for fi in fixed_indices:
            A_full.rows[fi] = [fi]
            A_full.data[fi] = [1.0]
            B_full.rows[fi] = [fi]
            B_full.data[fi] = [1.0]

        A = A_full.tocsc()
        B = B_full.tocsc()

        A_ff = A[free_indices, :][:, free_indices].tocsc()
        A_fF = A[free_indices, :][:, fixed_indices].tocsc()

        lu = spla.splu(A_ff)

        Tvec = T.ravel(order='C')
        Qvec = Qvol.ravel(order='C')

        RHS = B.dot(Tvec) + dt * (1.0 / (rho * cp)).ravel() * Qvec
        RHS[fixed_indices] = T0

        rhs_free = RHS[free_indices] - A_fF.dot(np.full(len(fixed_indices), T0))

        Tfree = lu.solve(rhs_free)
        Tvec[free_indices] = Tfree
        Tvec[fixed_indices] = T0

        T = Tvec.reshape((ny, nx), order='C')
        T_max = np.maximum(T_max, T)

        if (step % max(1, nt // 100) == 0) or step == nt: # plot every few steps
            plt.figure(fig_video.number)
            plt.clf()
            plt.title(f"PAW Temperature at t={t:.2f} s")
            plt.imshow(T, origin='lower', extent=[x[0]*1000, x[-1]*1000, y[0]*1000, y[-1]*1000], aspect='auto', cmap='hot')
            plt.colorbar(label='Temperature (K)')
            plt.xlabel('x (mm)')
            plt.ylabel('y (mm)')
            plt.pause(0.001)

            buf = BytesIO()
            fig_video.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            frame = imageio.imread(buf)
            frames.append(frame)
            buf.close()

        for i, (iy, ix) in enumerate(monitor_pts):
            T_history[i].append(T[iy, ix])

        if snapshot_time > 0 and t >= snapshot_time and not snapshot_taken:
            print(f"Taking snapshot at t={t:.2f}s")
            fusion_zone = T_max >= T_melt
            HAZ_zone = (T_max >= T_crit) & (T_max < T_melt)
            save_plots(T, T_max, x, y, X, Y, T_crit, T_melt, T0, midpoint, time_history, T_history, monitor_pts, mat_1, mat_2, fusion_zone, HAZ_zone, dx, dy, nx, ny, snapshot_name=f"_snapshot_{t:.2f}s")
            snapshot_taken = True
            print(f"Reached snapshot time at t={t:.2f}s.")

    if frames:
        print(f"Saving video to {video_filename}...")
        # Ensure all frames have the same size
        target_size = (frames[0].shape[1], frames[0].shape[0])
        resized_frames = []
        for frame in frames:
            if frame.shape[:2] != frames[0].shape[:2]:
                img = Image.fromarray(frame)
                img = img.resize(target_size, Image.Resampling.LANCZOS)
                resized_frames.append(np.array(img))
            else:
                resized_frames.append(frame)
        imageio.mimsave(video_filename, resized_frames, fps=10, format='FFMPEG', codec='libx264')
        print(f"Video saved successfully: {video_filename}")

    elapsed_time = time.time() - start_time
    print(f"Simulation: {elapsed_time:.1f}s")

    fusion_zone = T_max >= T_melt
    HAZ_zone = (T_max >= T_crit) & (T_max < T_melt)

    cell_area = dx * dy
    fusion_area = fusion_zone.sum() * cell_area
    HAZ_area = HAZ_zone.sum() * cell_area

    print(f"Peak Temp: {T_max.max():.1f}K")
    print(f"Fusion Area: {fusion_area*1e6:.2f}mm², HAZ: {HAZ_area*1e6:.2f}mm²")

    # Ensure final plots are saved
    if not snapshot_taken:
        save_plots(T, T_max, x, y, X, Y, T_crit, T_melt, T0, midpoint, time_history, T_history, monitor_pts, mat_1, mat_2, fusion_zone, HAZ_zone, dx, dy, nx, ny, snapshot_name="_final")
    else:
        save_plots(T, T_max, x, y, X, Y, T_crit, T_melt, T0, midpoint, time_history, T_history, monitor_pts, mat_1, mat_2, fusion_zone, HAZ_zone, dx, dy, nx, ny, snapshot_name="_final")

    # The save_plots function is now called only at snapshot_time
    # plt.show() # Removed to prevent blocking

def main():
    """Main function to run the simulation."""
    config_file = "/media/dell/Hard Drive/Summer of code/MME/ERW-pipelines/welding-kar/paw/config.json"
    with open(config_file, 'r') as f:
        data = json.load(f)

    sim_params = data['simulation_parameters']
    mat1_params = data['material_1']
    mat2_params = data['material_2']

    config = SimulationConfig(
        Lx=sim_params['Lx'],
        Ly=sim_params['Ly'],
        thickness=sim_params['thickness'],
        nx=sim_params['nx'],
        ny=sim_params['ny'],
        mat_1_name=mat1_params['name'],
        mat_1_rho=mat1_params['rho'],
        mat_1_cp=mat1_params['cp'],
        mat_1_k=mat1_params['k'],
        mat_1_T_melt=mat1_params['T_melt'],
        mat_1_T_crit=mat1_params['T_crit'],
        mat_2_name=mat2_params['name'],
        mat_2_rho=mat2_params['rho'],
        mat_2_cp=mat2_params['cp'],
        mat_2_k=mat2_params['k'],
        mat_2_T_melt=mat2_params['T_melt'],
        mat_2_T_crit=mat2_params['T_crit'],
        Q_paw=sim_params['Q_paw'],
        R_paw=sim_params['R_paw'],
        H_paw=sim_params['H_paw'],
        v_weld=sim_params['v_weld'],
        weld_x_position=sim_params['weld_x_position'],
        weld_start_y=sim_params['weld_start_y'],
        T0=sim_params['T0'],
        h_conv=sim_params['h_conv'],
        dt=sim_params['dt'],
        theta=sim_params['theta'],
        snapshot_time=sim_params['snapshot_time']
    )
    run_simulation(config)

if __name__ == "__main__":
    main()