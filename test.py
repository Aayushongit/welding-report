# welding_2d_cn_gaussian.py
# 2D transient heat conduction with a moving Gaussian surface heat source
# Crank-Nicolson implicit scheme, sparse matrices (SciPy)
#
# Requirements:
#   pip install numpy scipy matplotlib imageio imageio-ffmpeg pillow

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import matplotlib.pyplot as plt
import time
import imageio.v2 as imageio
from io import BytesIO
from PIL import Image

# -------------------- domain & mesh --------------------
Lx = 0.12      # m
Ly = 0.06      # m
nx = 121
ny = 61
x = np.linspace(0, Lx, nx)
y = np.linspace(-Ly/2, Ly/2, ny)
X, Y = np.meshgrid(x, y)   # shape (ny, nx)

dx = x[1] - x[0]
dy = y[1] - y[0]
N = nx * ny

# helper to map (i,j) -> index in flattened vector (row-major)
def idx(i, j):
    return j * nx + i

# -------------------- material & initial --------------------
rho = 7850.0            # kg/m3
cp = 500.0              # J/kg.K
k = 45.0                # W/m.K
alpha = k / (rho * cp)

T0 = 293.0              # K
T = np.full((ny, nx), T0)
Tmax = T.copy()

# -------------------- heat source params --------------------
P = 2000.0              # W
eta = 0.8
sigma = 0.005           # m
dp = 0.002              # m, effective penetration depth to convert surface q to volumetric Q
v = 0.01                # m/s welding speed
x_start = 0.01
y_source = 0.0

Qtot = eta * P

# -------------------- time stepping --------------------
t_end = (Lx - x_start) / v + 0.5
dt = 0.02
nt = int(np.ceil(t_end / dt))
theta = 0.5  # 0.5 = Crank-Nicolson

# -------------------- build 2D Laplacian (sparse) --------------------
ex = np.ones(nx)
ey = np.ones(ny)
Tx = sp.diags([ex, -2*ex, ex], [-1, 0, 1], shape=(nx, nx)) / dx**2
Ty = sp.diags([ey, -2*ey, ey], [-1, 0, 1], shape=(ny, ny)) / dy**2
Ix = sp.eye(nx, format='csc')
Iy = sp.eye(ny, format='csc')

L = sp.kron(Iy, Tx, format='csc') + sp.kron(Ty, Ix, format='csc')  # NxN

# -------------------- Dirichlet boundary nodes (fixed to T0) --------------------
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

# -------------------- matrices A and B --------------------
I = sp.eye(N, format='csc')
A_full = (I - theta * dt * alpha * L).tolil()
B_full = (I + (1 - theta) * dt * alpha * L).tolil()

# enforce Dirichlet rows in A and B (set row -> unit vector, RHS will use T0)
for fi in fixed_indices:
    A_full.rows[fi] = [fi]
    A_full.data[fi] = [1.0]
    B_full.rows[fi] = [fi]
    B_full.data[fi] = [1.0]

A = A_full.tocsc()
B = B_full.tocsc()

# Extract subblocks needed for solving
A_ff = A[free_indices, :][:, free_indices].tocsc()      # free x free
A_fF = A[free_indices, :][:, fixed_indices].tocsc()     # free x fixed

# LU factorization of A_ff (reuse each time step)
lu = spla.splu(A_ff)

# -------------------- video recording setup --------------------
frames = []  # list to store video frames
video_filename = "welding_simulation.mp4"
fig = plt.figure(figsize=(10, 6))  # Fixed figure size for consistent video frames

# -------------------- time loop --------------------
t = 0.0
start_time = time.time()
print("Simulating steps:", nt)
for step in range(1, nt + 1):
    t += dt
    xs = x_start + v * t
    
    # Gaussian surface heat at previous and current time (W/m^2), then convert to volumetric W/m^3
    Qn = (Qtot / (2 * np.pi * sigma**2)) * np.exp(-(((X - (xs - v*dt))**2 + (Y - y_source)**2) / (2 * sigma**2)))
    Qnp1 = (Qtot / (2 * np.pi * sigma**2)) * np.exp(-(((X - xs)**2 + (Y - y_source)**2) / (2 * sigma**2)))
    Qvol = 0.5 * (Qn + Qnp1) / dp
    
    Tvec = T.ravel(order='C')   # length N, row-major
    Qvec = Qvol.ravel(order='C')
    
    RHS = B.dot(Tvec) + dt * (1.0 / (rho * cp)) * Qvec
    
    # enforce Dirichlet values in RHS for fixed nodes
    RHS[fixed_indices] = T0
    
    # compute RHS for free block accounting for fixed node contributions:
    rhs_free = RHS[free_indices] - A_fF.dot(np.full(len(fixed_indices), T0))
    
    # solve for free nodes
    Tfree = lu.solve(rhs_free)
    # assemble new Tvec
    Tvec[free_indices] = Tfree
    Tvec[fixed_indices] = T0
    T = Tvec.reshape((ny, nx), order='C')
    Tmax = np.maximum(Tmax, T)
    
    # occasional plotting status
    if (step % max(1, nt // 30) == 0) or step == 1 or step == nt:
        print(f"step {step}/{nt}, t={t:.3f}s, source x={xs:.4f}m")
        plt.figure(fig.number)
        plt.clf()
        plt.title(f"T at t={t:.2f} s")
        im = plt.imshow(T, origin='lower', extent=[x[0], x[-1], y[0], y[-1]], aspect='auto', cmap='hot')
        plt.colorbar(im)
        plt.xlabel('x (m)')
        plt.ylabel('y (m)')
        plt.pause(0.001)

        # Capture frame for video
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        frame = imageio.imread(buf)
        frames.append(frame)
        buf.close()

print("Simulation finished in {:.1f}s".format(time.time() - start_time))

# -------------------- save video --------------------
if frames:
    print(f"Saving video to {video_filename}...")
    # Ensure all frames have the same size (use first frame size as reference)
    target_size = (frames[0].shape[1], frames[0].shape[0])  # (width, height)
    resized_frames = []
    for frame in frames:
        if frame.shape[:2] != frames[0].shape[:2]:
            # Convert to PIL Image, resize, and convert back to numpy array
            img = Image.fromarray(frame)
            img = img.resize(target_size, Image.Resampling.LANCZOS)
            resized_frames.append(np.array(img))
        else:
            resized_frames.append(frame)

    imageio.mimsave(video_filename, resized_frames, fps=10, format='FFMPEG', codec='libx264')
    print(f"Video saved successfully: {video_filename}")
else:
    print("No frames captured for video.")

# -------------------- postprocess: HAZ --------------------
T_HAZ = 873.0    # K, example threshold (~600°C)
mask_HAZ = Tmax >= T_HAZ

plt.figure()
contour_plot = plt.contourf(x, y, Tmax, levels=40, cmap='hot')
plt.contour(x, y, mask_HAZ, levels=[0.5], colors='k', linewidths=1.2)
plt.title("Peak temperature and HAZ contour")
plt.xlabel("x (m)")
plt.ylabel("y (m)")
plt.colorbar(contour_plot, label='K')
plt.show()

# HAZ area estimate
area_per_cell = dx * dy
haz_area = mask_HAZ.sum() * area_per_cell
print(f"Estimated HAZ area (m^2): {haz_area:.6e}")
