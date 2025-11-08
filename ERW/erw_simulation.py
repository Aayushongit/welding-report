import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import os
import time
from dataclasses import dataclass
import json
from numba import njit
import seaborn as sns
import imageio.v2 as imageio
from io import BytesIO
from PIL import Image

@dataclass
class SimulationConfig:
    """Configuration for ERW pipe welding simulation"""
    Lx: float  # Domain length (m)
    Ly: float  # Domain width (m)
    thickness: float  # Pipe wall thickness (m)
    nx: int  # Grid points in x
    ny: int  # Grid points in y

    # Material properties
    mat_name: str
    mat_rho: float  # Density (kg/m³)
    mat_cp: float  # Specific heat (J/kg·K)
    mat_k: float  # Thermal conductivity (W/m·K)
    mat_sigma_e: float  # Electrical conductivity (S/m)
    mat_T_melt: float  # Melting temperature (K)
    mat_T_crit: float  # Critical temperature for HAZ (K)
    mat_resistivity: float  # Electrical resistivity (Ω·m)

    # ERW process parameters
    Q_power: float  # Total welding power (W)
    eta_erw: float  # Process efficiency
    R_contact_init: float  # Initial contact resistance (Ω·m²)
    contact_width: float  # Contact zone width (m)
    v_weld: float  # Welding speed (m/s)
    x_start: float  # Starting x position
    y_start: float  # Starting y position
    frequency: float  # AC frequency (Hz)
    current_density: float  # Current density (A/m²)

    # Thermal boundary conditions
    T0: float  # Ambient temperature (K)
    h_conv: float  # Convection coefficient (W/m²·K)

    # Numerical parameters
    dt: float  # Time step (s)
    theta: float  # Time integration parameter (0.5=Crank-Nicolson)
    snapshot_time: float  # Time for snapshot (s)

    # Contact model parameters
    R_c_base: float
    pressure_ref: float
    temp_melt_factor: float
    asperity_reduction: float

    # Phase kinetics parameters
    Ms_martensite: float
    alpha_KM: float
    K0_JMAK: float
    n_JMAK: float
    Ea_JMAK: float

class Material:
    """Material properties for pipe steel"""
    def __init__(self, name, rho, cp, k, sigma_e, T_melt, T_crit, resistivity):
        self.name = name
        self.rho = rho
        self.cp = cp
        self.k = k
        self.sigma_e = sigma_e
        self.alpha = k / (rho * cp)
        self.T_melt = T_melt
        self.T_crit = T_crit
        self.resistivity = resistivity

def erw_contact_resistance(T, pressure, R_c_base, T_melt, pressure_ref, temp_melt_factor):
    """
    Contact resistance model for ERW pipe seam
    Accounts for temperature and pressure effects
    """
    # Pressure effect: higher pressure reduces resistance
    pressure_factor = np.sqrt(pressure_ref / np.maximum(pressure, 1e6))

    # Temperature effect: resistance drops near melting
    temp_ratio = T / T_melt
    temp_factor = np.where(temp_ratio < 0.8, 1.0,
                          np.where(temp_ratio < 1.0,
                                  1.0 - (temp_ratio - 0.8) / 0.2 * (1.0 - temp_melt_factor),
                                  temp_melt_factor))

    return R_c_base * pressure_factor * temp_factor

def erw_joule_heating(X, Y, x_arc, y_arc, current_density, sigma_e, R_contact, contact_width, eta):
    """
    ERW Joule heating model - combines contact resistance heating and bulk Joule heating

    Contact heating dominates at the seam interface
    Q = I² * R_c concentrated at the contact zone
    Plus volumetric Joule heating Q = σ_e * E² in bulk
    """
    # Contact zone heating (concentrated at seam)
    r_sq = (X - x_arc)**2 + (Y - y_arc)**2
    contact_zone = np.exp(-r_sq / (contact_width**2))

    # Current density distribution (Gaussian near seam)
    J_local = current_density * contact_zone

    # Volumetric Joule heating: Q = J² / σ_e
    Q_bulk = (J_local**2) / (sigma_e + 1e-10)

    # Contact resistance heating (surface heat flux converted to volumetric)
    # Surface power density: q_c = J² * R_c
    # Spread over small thickness to get volumetric source
    thickness_contact = contact_width / 3.0
    Q_contact = (J_local**2) * R_contact / thickness_contact

    # Total heating with efficiency factor
    Q_total = eta * (Q_bulk + Q_contact)

    return Q_total

@njit
def get_k(T, k_base, T_crit, T_melt):
    """Temperature-dependent thermal conductivity"""
    if T < T_crit:
        return k_base
    elif T < T_melt:
        # Increase in HAZ region
        return k_base * (1 + (T - T_crit) / (T_melt - T_crit) * 0.15)
    else:
        # Molten region
        return k_base * 1.15

@njit
def get_cp(T, cp_base, T_crit, T_melt):
    """Temperature-dependent specific heat"""
    if T < T_crit:
        return cp_base
    elif T < T_melt:
        # Increase in HAZ region (phase transformation)
        return cp_base * (1 + (T - T_crit) / (T_melt - T_crit) * 0.3)
    else:
        # Molten region
        return cp_base * 1.3

@njit
def get_rho(T, rho_base, T_crit, T_melt):
    """Temperature-dependent density"""
    if T < T_crit:
        return rho_base
    elif T < T_melt:
        # Decrease with temperature
        return rho_base * (1 - (T - T_crit) / (T_melt - T_crit) * 0.03)
    else:
        # Molten region
        return rho_base * 0.97

@njit
def get_sigma_e(T, sigma_base, T_crit, T_melt):
    """Temperature-dependent electrical conductivity"""
    if T < T_crit:
        # Decrease with temperature (normal behavior)
        return sigma_base * (1 - (T - 300) / (T_crit - 300) * 0.3)
    elif T < T_melt:
        # Continue decreasing
        return sigma_base * 0.7 * (1 - (T - T_crit) / (T_melt - T_crit) * 0.4)
    else:
        # Molten metal
        return sigma_base * 0.42

def compute_martensite_fraction(T_peak, cooling_rate, Ms, alpha_KM):
    """
    Koistinen-Marburger model for martensite formation
    X_M = 1 - exp(-α(Ms - T))
    """
    if T_peak < Ms:
        return 0.0

    # Effective quenching temperature (depends on cooling rate)
    T_eff = Ms - 50 * np.log10(np.maximum(cooling_rate, 1.0))

    if T_eff > Ms:
        X_M = 1 - np.exp(-alpha_KM * (Ms - T_eff))
        return np.clip(X_M, 0.0, 1.0)
    return 0.0

def save_plots(T, T_max, x, y, X, Y, T_crit, T_melt, T0, midpoint, time_history,
               T_history, monitor_pts, material, fusion_zone, HAZ_zone, dx, dy,
               nx, ny, snapshot_name=""):
    """Generate comprehensive visualization plots for ERW simulation (17 plots matching EBW)"""

    sns.set_theme(style="whitegrid")
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Define detailed isotherms
    isotherm_levels_detailed = np.array([400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1273,
                                         1400, 1500, 1600, 1767, 1900, 2000, 2100, 2200])
    isotherm_levels_detailed = isotherm_levels_detailed[isotherm_levels_detailed < T_max.max()]

    # Color coding for isotherms
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

    # Plot 1: Detailed Temperature Isotherms
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
    ax1.set_title('Detailed Temperature Isotherms\n(Blue=Cool, Orange=HAZ, Red=Fusion)',
                  fontsize=12, fontweight='bold')
    cbar1 = plt.colorbar(im1, ax=ax1, label='Temperature (K)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'1_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')

    # Plot 2: Isotherm-Only View
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
    ax2.set_title('Isotherm-Only View\n(Cyan=HAZ boundary, White=Fusion boundary)',
                  fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.2)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'2_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')

    # Plot 3: Color-Coded Isotherm Families
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
    ax3.set_title('Color-Coded Isotherm Families\n(Blue=Cool, Orange=HAZ, Red=Fusion)',
                  fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'3_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')

    # Plot 4: Temperature Gradient Magnitude
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
    ax4.set_title('Temperature Gradient Magnitude\n(Shows heat flow patterns)',
                  fontsize=12, fontweight='bold')
    plt.colorbar(im4, ax=ax4, label='|∇T| (K/m)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'4_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')

    # Plot 5: Fusion Zone & HAZ Regions
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
    ax5.set_title('Fusion Zone & HAZ Regions\n(with boundary isotherms)',
                  fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'5_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')

    # Plot 6: Centerline Temperature
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
    ax6.set_title('Centerline Temperature\n(with isotherm levels)',
                  fontsize=12, fontweight='bold')
    ax6.legend(fontsize=9, loc='upper right')
    ax6.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'6_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')

    # Plot 7: Transverse Temperature Profile
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
    ax7.set_title('Transverse Temperature Profile\nat Weld Center',
                  fontsize=12, fontweight='bold')
    ax7.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'7_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')

    # Plot 8: Weld Width Along Length
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
            ax8.axhline(np.mean(weld_widths), color='red', linestyle='--', linewidth=2,
                       label=f'Avg: {np.mean(weld_widths):.2f}mm')
            ax8.set_xlabel('x (mm)', fontsize=11)
            ax8.set_ylabel('Width (mm)', fontsize=11)
            ax8.set_title('Weld Width Along Length', fontsize=12, fontweight='bold')
            ax8.legend(fontsize=9)
            ax8.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'8_plot{snapshot_name}.png'), dpi=300, bbox_inches='tight')

    # Plot 9: Temperature (°C) with Isotherms
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

    # Plot 10: 3D Peak Temperature
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

    # Plot 11: 3D with Isotherm Projections
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

    # Plot 12: 3D Zones Scatter
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

    # Plot 13: 3D Temperature Gradient
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

    # Plot 14: Thermal Cycles
    fig14 = plt.figure(figsize=(8, 6), num='14. Thermal Cycle 1')
    plt.clf()
    ax1_tc = fig14.add_subplot(111)
    colors_tc = ['blue', 'red', 'green', 'purple']
    for i, (iy, ix) in enumerate(monitor_pts):
        ax1_tc.plot(time_history, T_history[i], color=colors_tc[i % len(colors_tc)], linewidth=2,
                   label=f'Pt{i+1}: ({x[ix]*1000:.1f},{y[iy]*1000:.1f})mm - {material.name}')

    for temp in [T_crit, T_melt]:
        ax1_tc.axhline(temp, linestyle='--', linewidth=2, alpha=0.6)

    ax1_tc.set_xlabel('Time (s)', fontsize=11)
    ax1_tc.set_ylabel('Temperature (K)', fontsize=11)
    ax1_tc.set_title('Thermal Cycles', fontsize=12, fontweight='bold')
    ax1_tc.legend(fontsize=9)
    ax1_tc.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'14_thermal_cycle{snapshot_name}.png'), dpi=300, bbox_inches='tight')

    # Plot 15: Cooling Rates
    fig15 = plt.figure(figsize=(8, 6), num='15. Thermal Cycle 2')
    plt.clf()
    ax2_tc = fig15.add_subplot(111)
    for i, (iy, ix) in enumerate(monitor_pts):
        T_hist = np.array(T_history[i])
        if len(T_hist) > 10:
            cooling_rate = np.gradient(T_hist, time_history)
            ax2_tc.plot(time_history, cooling_rate, color=colors_tc[i % len(colors_tc)], linewidth=2,
                       label=f'Pt{i+1} - {material.name}')

    ax2_tc.axhline(0, color='black', linestyle='-', linewidth=0.5)
    ax2_tc.set_xlabel('Time (s)', fontsize=11)
    ax2_tc.set_ylabel('Cooling Rate (K/s)', fontsize=11)
    ax2_tc.set_title('Cooling Rates', fontsize=12, fontweight='bold')
    ax2_tc.legend(fontsize=9)
    ax2_tc.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'15_thermal_cycle{snapshot_name}.png'), dpi=300, bbox_inches='tight')

    # Plot 16: Final Temperature
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

    # Plot 17: Peak T vs Position
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
    plt.close('all')

def run_simulation(config: SimulationConfig):
    """Main ERW simulation runner"""

    print("=" * 70)
    print("ERW (Electric Resistance Welding) Pipe Simulation")
    print("=" * 70)

    # Unpack configuration
    Lx, Ly, thickness = config.Lx, config.Ly, config.thickness
    nx, ny = config.nx, config.ny
    Q_power = config.Q_power
    eta_erw = config.eta_erw
    R_contact_init = config.R_contact_init
    contact_width = config.contact_width
    v_weld = config.v_weld
    x_start = config.x_start
    y_start = config.y_start
    T0 = config.T0
    h_conv = config.h_conv
    dt = config.dt
    theta = config.theta
    snapshot_time = config.snapshot_time

    # Create material
    material = Material(config.mat_name, config.mat_rho, config.mat_cp,
                       config.mat_k, config.mat_sigma_e, config.mat_T_melt,
                       config.mat_T_crit, config.mat_resistivity)

    # Setup grid
    x = np.linspace(0, Lx, nx)
    y = np.linspace(-Ly/2, Ly/2, ny)
    X, Y = np.meshgrid(x, y)

    dx = x[1] - x[0]
    dy = y[1] - y[0]
    N = nx * ny

    midpoint = Lx / 2  # Weld seam centerline

    T_melt = material.T_melt
    T_crit = material.T_crit

    print(f"Grid: {nx} x {ny} = {N} nodes")
    print(f"Domain: {Lx*1000:.1f} mm x {Ly*1000:.1f} mm")
    print(f"Material: {material.name}")
    print(f"Power: {Q_power:.0f} W, Efficiency: {eta_erw*100:.1f}%")
    print(f"Welding speed: {v_weld*1000:.2f} mm/s")
    print(f"Contact width: {contact_width*1000:.2f} mm")
    print(f"Frequency: {config.frequency/1000:.0f} kHz")

    # Determine simulation end time
    if snapshot_time > 0:
        t_end = snapshot_time
    else:
        t_end = Ly / v_weld + 5.0

    nt = int(np.ceil(t_end / dt))
    print(f"Time steps: {nt}, Total time: {t_end:.2f} s")
    print("=" * 70)

    # Build Laplacian operator
    def idx(i, j):
        return j * nx + i

    ex = np.ones(nx)
    ey = np.ones(ny)
    Tx = sp.diags([ex, -2*ex, ex], [-1, 0, 1], shape=(nx, nx)) / dx**2
    Ty = sp.diags([ey, -2*ey, ey], [-1, 0, 1], shape=(ny, ny)) / dy**2
    Ix = sp.eye(nx, format='csc')
    Iy = sp.eye(ny, format='csc')

    L = sp.kron(Iy, Tx, format='csc') + sp.kron(Ty, Ix, format='csc')

    # Boundary conditions (fixed at ambient temperature)
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

    # Initialize temperature field
    T = np.full((ny, nx), T0)
    T_max = T.copy()

    # Monitoring points
    monitor_pts = [
        (ny // 2, nx // 4),      # Left of seam
        (ny // 2, nx // 2),      # At seam
        (ny // 2, 3 * nx // 4),  # Right of seam
        (3 * ny // 4, nx // 2),  # Above seam
    ]
    T_history = {i: [] for i in range(len(monitor_pts))}
    time_history = []

    # Time integration
    t = 0.0
    start_time = time.time()
    snapshot_taken = False
    frames = []
    video_filename = "erw_simulation.mp4"
    fig_video = plt.figure(figsize=(10, 7))

    print("Starting time integration...")
    print_interval = max(1, nt // 20)

    for step in range(1, nt + 1):
        t += dt
        time_history.append(t)

        # Moving heat source (welding along y-axis at x = midpoint)
        current_x_arc = midpoint
        current_y_arc = y_start + v_weld * t

        # Estimate local pressure (simplified model)
        pressure = config.pressure_ref * np.ones_like(X)

        # Compute contact resistance (temperature-dependent)
        R_contact = erw_contact_resistance(T, pressure, config.R_c_base,
                                          T_melt, config.pressure_ref,
                                          config.temp_melt_factor)
        R_contact_scalar = np.mean(R_contact)

        # Generate heat source
        if current_y_arc <= Ly/2:
            Qvol = erw_joule_heating(X, Y, current_x_arc, current_y_arc,
                                    config.current_density, material.sigma_e,
                                    R_contact_scalar, contact_width, eta_erw)
        else:
            Qvol = np.zeros_like(X)

        # Update material properties
        k_vec = np.vectorize(get_k)
        cp_vec = np.vectorize(get_cp)
        rho_vec = np.vectorize(get_rho)

        k = k_vec(T, material.k, T_crit, T_melt)
        cp = cp_vec(T, material.cp, T_crit, T_melt)
        rho = rho_vec(T, material.rho, T_crit, T_melt)
        alpha = k / (rho * cp)

        # Assemble system matrices
        I_mat = sp.eye(N, format='csc')
        A_full = (I_mat - theta * dt * sp.diags(alpha.ravel()) * L).tolil()
        B_full = (I_mat + (1 - theta) * dt * sp.diags(alpha.ravel()) * L).tolil()

        # Apply boundary conditions
        for fi in fixed_indices:
            A_full.rows[fi] = [fi]
            A_full.data[fi] = [1.0]
            B_full.rows[fi] = [fi]
            B_full.data[fi] = [1.0]

        A = A_full.tocsc()
        B = B_full.tocsc()

        A_ff = A[free_indices, :][:, free_indices].tocsc()
        A_fF = A[free_indices, :][:, fixed_indices].tocsc()

        # Solve linear system
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

        # Record monitoring points
        for i, (iy, ix) in enumerate(monitor_pts):
            T_history[i].append(T[iy, ix])

        # Generate video frame
        if (step % max(1, nt // 100) == 0) or step == nt:
            plt.figure(fig_video.number)
            plt.clf()
            plt.title(f"ERW Temperature at t={t:.2f} s\nWelding Speed: {v_weld*1000:.1f} mm/s, Power: {Q_power:.0f} W",
                     fontsize=12, fontweight='bold')
            plt.imshow(T, origin='lower',
                      extent=[x[0]*1000, x[-1]*1000, y[0]*1000, y[-1]*1000],
                      aspect='auto', cmap='hot', vmin=T0, vmax=T_max.max())
            plt.colorbar(label='Temperature (K)')
            plt.xlabel('x (mm)', fontsize=11)
            plt.ylabel('y (mm)', fontsize=11)
            plt.axvline(midpoint*1000, color='cyan', linestyle='--', linewidth=2, alpha=0.7)

            # Mark current welding position
            if current_y_arc <= Ly/2:
                plt.plot(current_x_arc*1000, current_y_arc*1000, 'w*',
                        markersize=15, markeredgecolor='red', markeredgewidth=1.5)

            plt.tight_layout()

            buf = BytesIO()
            fig_video.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            frame = imageio.imread(buf)
            frames.append(frame)
            buf.close()

        # Progress reporting
        if step % print_interval == 0:
            progress = step / nt * 100
            T_peak = T_max.max()
            print(f"Step {step}/{nt} ({progress:.1f}%) | t={t:.2f}s | Peak T={T_peak:.1f}K | Arc pos: {current_y_arc*1000:.1f}mm")

        # Snapshot at specified time
        if snapshot_time > 0 and t >= snapshot_time and not snapshot_taken:
            print(f"\nTaking snapshot at t={t:.2f}s...")
            fusion_zone = T_max >= T_melt
            HAZ_zone = (T_max >= T_crit) & (T_max < T_melt)
            save_plots(T, T_max, x, y, X, Y, T_crit, T_melt, T0, midpoint,
                      time_history, T_history, monitor_pts, material,
                      fusion_zone, HAZ_zone, dx, dy, nx, ny,
                      snapshot_name=f"_snapshot_{t:.2f}s")
            snapshot_taken = True
            print(f"Snapshot saved at t={t:.2f}s\n")

    plt.close(fig_video)

    # Save video
    if frames:
        print(f"\nSaving video to {video_filename}...")
        target_size = (frames[0].shape[1], frames[0].shape[0])
        resized_frames = []
        for frame in frames:
            if frame.shape[:2] != frames[0].shape[:2]:
                img = Image.fromarray(frame)
                img = img.resize(target_size, Image.Resampling.LANCZOS)
                resized_frames.append(np.array(img))
            else:
                resized_frames.append(frame)

        imageio.mimsave(video_filename, resized_frames, fps=15,
                       format='FFMPEG', codec='libx264')
        print(f"Video saved successfully: {video_filename}")

    elapsed_time = time.time() - start_time
    print(f"\nSimulation completed in {elapsed_time:.1f} seconds")

    # Compute final statistics
    fusion_zone = T_max >= T_melt
    HAZ_zone = (T_max >= T_crit) & (T_max < T_melt)

    cell_area = dx * dy
    fusion_area = fusion_zone.sum() * cell_area
    HAZ_area = HAZ_zone.sum() * cell_area

    print("\n" + "=" * 70)
    print("SIMULATION RESULTS")
    print("=" * 70)
    print(f"Peak Temperature: {T_max.max():.1f} K ({T_max.max()-273.15:.1f} °C)")
    print(f"Fusion Zone Area: {fusion_area*1e6:.2f} mm²")
    print(f"HAZ Area: {HAZ_area*1e6:.2f} mm²")
    print(f"Total Affected Area: {(fusion_area + HAZ_area)*1e6:.2f} mm²")

    # Estimate weld width
    if fusion_zone.any():
        iy_center = ny // 2
        fusion_widths = []
        for i in range(nx):
            if fusion_zone[:, i].any():
                y_idx = np.where(fusion_zone[:, i])[0]
                if len(y_idx) > 1:
                    width = (y[y_idx[-1]] - y[y_idx[0]]) * 1000
                    fusion_widths.append(width)

        if fusion_widths:
            avg_width = np.mean(fusion_widths)
            print(f"Average Weld Width: {avg_width:.2f} mm")

    print("=" * 70)

    # Generate final plots
    if not snapshot_taken:
        save_plots(T, T_max, x, y, X, Y, T_crit, T_melt, T0, midpoint,
                  time_history, T_history, monitor_pts, material,
                  fusion_zone, HAZ_zone, dx, dy, nx, ny, snapshot_name="_final")
    else:
        save_plots(T, T_max, x, y, X, Y, T_crit, T_melt, T0, midpoint,
                  time_history, T_history, monitor_pts, material,
                  fusion_zone, HAZ_zone, dx, dy, nx, ny, snapshot_name="_final")

    print("\nAll results saved to output/ directory")
    print("Simulation complete!")

def main():
    """Load configuration and run ERW simulation"""

    config_file = "config.json"

    if not os.path.exists(config_file):
        config_file = "/media/dell/Hard Drive/Summer of code/MME/ERW-pipelines/welding-kar/ERW/config.json"

    print(f"Loading configuration from: {config_file}")

    with open(config_file, 'r') as f:
        data = json.load(f)

    sim_params = data['simulation_parameters']
    mat_params = data['material_pipe']
    contact_params = data['contact_model']
    phase_params = data['phase_kinetics']

    config = SimulationConfig(
        Lx=sim_params['Lx'],
        Ly=sim_params['Ly'],
        thickness=sim_params['thickness'],
        nx=sim_params['nx'],
        ny=sim_params['ny'],
        mat_name=mat_params['name'],
        mat_rho=mat_params['rho'],
        mat_cp=mat_params['cp'],
        mat_k=mat_params['k'],
        mat_sigma_e=mat_params['sigma_electrical'],
        mat_T_melt=mat_params['T_melt'],
        mat_T_crit=mat_params['T_crit'],
        mat_resistivity=mat_params['resistivity'],
        Q_power=sim_params['Q_power'],
        eta_erw=sim_params['eta_erw'],
        R_contact_init=sim_params['R_contact_init'],
        contact_width=sim_params['contact_width'],
        v_weld=sim_params['v_weld'],
        x_start=sim_params['x_start'],
        y_start=sim_params['y_start'],
        frequency=sim_params['frequency'],
        current_density=sim_params['current_density'],
        T0=sim_params['T0'],
        h_conv=sim_params['h_conv'],
        dt=sim_params['dt'],
        theta=sim_params['theta'],
        snapshot_time=sim_params['snapshot_time'],
        R_c_base=contact_params['R_c_base'],
        pressure_ref=contact_params['pressure_ref'],
        temp_melt_factor=contact_params['temp_melt_factor'],
        asperity_reduction=contact_params['asperity_reduction'],
        Ms_martensite=phase_params['Ms_martensite'],
        alpha_KM=phase_params['alpha_KM'],
        K0_JMAK=phase_params['K0_JMAK'],
        n_JMAK=phase_params['n_JMAK'],
        Ea_JMAK=phase_params['Ea_JMAK']
    )

    run_simulation(config)

if __name__ == "__main__":
    main()
