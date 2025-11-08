# Mathematical modeling report — ERW (Electric-Resistance Welding) for pipeline seams

*(focused on the mathematics & theory; ready to be implemented in FEM / FDM codes)*

---

## 1 — Executive summary (what this report gives)

A rigorous, implementable mathematical framework to simulate the ERW pipe-seam process. It covers:

* governing PDEs (electro-thermal, thermo-mechanical, phase-kinetics),
* contact / interface resistance modeling (source of Joule heating),
* constitutive relations and metallurgical kinetics (JMAK, Koistinen–Marburger),
* boundary / initial conditions appropriate for pipe ERW,
* numerical solution strategies (staggered coupling, fully coupled schemes),
* parameter estimation and validation notes.

Key background results used in thermal modelling (moving heat source / Rosenthal family) and contact resistance modelling are standard in welding literature. ([ScienceDirect][1])

---

## 2 — Physics and modelling assumptions (typical for ERW pipes)

1. Continuum mechanics & heat transfer; material properties are temperature-dependent: (k(T),;c_p(T),;\rho(T),;\sigma_e(T)) (electrical conductivity).
2. Welding current is large and quasi-static (electromagnetics solved in electrostatic approximation). Magnetic effects (induction) included if HF-ERW requires high frequency modeling. ([ScienceDirect][2])
3. Geometry: thin pipe wall → option to use 2D axisymmetric shell or full 3D near the seam where 3D gradients matter.
4. Contact interface between the two edges: has an evolving contact resistance (R_c(t,x)) representing asperity conduction, oxidation, melting. Contact area depends on pressure and temperature. Contact heating dominates bulk Joule heating. ([SpringerLink][3])

---

## 3 — Governing equations

### 3.1 Electrical conduction (quasi-static)

Let (\phi(\mathbf{x},t)) be the electric potential. Current density:
[
\mathbf{J}(\mathbf{x},t) = -\sigma_e(T),\nabla\phi.
]
Conservation of charge (steady in quasistatic):
[
\nabla\cdot\big(\sigma_e(T),\nabla\phi\big)=0 \qquad\text{in the conductor domain}, \Omega.
]
Boundary conditions: prescribed net current (I(t)) through electrodes / rollers, or prescribed potential on electrodes. At free surfaces: insulating (\mathbf{n}\cdot\mathbf{J}=0) (unless external circuits present).

**Interface (contact) electrical model** (lumped thin layer): across the interface (\Gamma_c),
[
\mathbf{n}\cdot\big(\sigma_e\nabla\phi\big)\big|*{\Gamma_c^-} - \mathbf{n}\cdot\big(\sigma_e\nabla\phi\big)\big|*{\Gamma_c^+} = \frac{\phi^- - \phi^+}{R_c(A_r,T,p)}
]
or equivalently treat (R_c) as a thin resistor per unit area giving a jump in normal flux. (R_c) depends on real contact area (A_r), temperature and normal pressure (p). Review of contact resistance models: see Hamedi et al. and contact literature. ([SpringerLink][3])

Joule heating volumetric source (for thermal PDE):
[
Q_{\rm Joule}(\mathbf{x},t)=\mathbf{J}\cdot\mathbf{E}=\sigma_e(T),|\nabla\phi|^2.
]
If contact heating is concentrated, you may represent it as surface power density (q_c = I^2R_c) on (\Gamma_c) or spread over a thin layer of thickness (\delta).

---

### 3.2 Transient heat conduction (energy)

[
\rho(T)c_p(T),\frac{\partial T}{\partial t}
= \nabla\cdot\big(k(T)\nabla T\big) + Q_{\rm Joule}(\mathbf{x},t) + Q_{\text{mech}} - q_{\rm loss},
]
where

* (Q_{\text{mech}}) is heat generation from plastic work (often (\beta,\boldsymbol{\sigma}:\dot{\boldsymbol{\varepsilon}}_\text{pl}) with (\beta) the Taylor–Quinney factor ∼0.9),
* (q_{\rm loss}) includes convection and radiation on external surfaces:
  [
  q_{\rm loss}=h,(T-T_\infty) + \varepsilon\sigma_{\rm SB}(T^4-T_\infty^4).
  ]

**Moving source modelling:** for process-level models, approximate (Q_{\rm Joule}) with a moving Gaussian/ellipsoidal distribution concentrated at seam:
[
Q(x,y,z,t)\approx \frac{P(t)}{(2\pi)^{3/2}\sigma_x\sigma_y\sigma_z}
\exp!\Big(-\frac{(x-vt)^2}{2\sigma_x^2}-\frac{y^2}{2\sigma_y^2}-\frac{z^2}{2\sigma_z^2}\Big),
]
where (P(t)) is power per unit length (or area), (v) is welding speed. Analytical moving-source solutions (Rosenthal) are available for simplified geometries and are useful for quick estimates. ([ScienceDirect][1])

---

### 3.3 Mechanics (thermo-elastic-plastic)

Balance of linear momentum (quasi-static during rolling):
[
\nabla\cdot\boldsymbol{\sigma} + \mathbf{b} = \mathbf{0},
]
strain decomposition:
[
\boldsymbol{\varepsilon} = \boldsymbol{\varepsilon}^\text{el} + \boldsymbol{\varepsilon}^\text{pl} + \boldsymbol{\varepsilon}^\text{th},\qquad
\boldsymbol{\varepsilon}^\text{th}=\alpha(T-T_0)\mathbf{I}.
]
Constitutive law (small strains):
[
\boldsymbol{\sigma} = \mathbb{C}(T,\text{phases}):(\boldsymbol{\varepsilon}-\boldsymbol{\varepsilon}^\text{pl}-\boldsymbol{\varepsilon}^\text{th}),
]
with plasticity evolution (e.g., von Mises with isotropic/kinematic hardening):
[
\dot{\boldsymbol{\varepsilon}}^\text{pl} = \dot{\gamma},\frac{\mathbf{s}}{|\mathbf{s}|},\quad \text{with yield } f(\boldsymbol{\sigma},\kappa)=0.
]
Rolling pressure (p(t,x)) is applied boundary traction on the contact zone. The mechanical solution influences real contact area (A_r) (via local contact pressure and surface topography models), which closes the loop to (R_c).

---

### 3.4 Phase transformation kinetics (metallurgy)

**Diffusional transformations (pearlite, bainite):** JMAK (Johnson-Mehl-Avrami-Kolmogorov) type:
[
X(t)=1-\exp\big(-K(T),t^{,n}\big),\quad K(T)=K_0\exp!\Big(-\frac{E_a}{RT}\Big),
]
for isothermal conditions; for non-isothermal continuous cooling use local time–temperature path and incremental integration (modified JMAK or additively integrate nucleation/growth rates). ([ScienceDirect][4])

**Athermal martensite:** Koistinen–Marburger (KM) empirical relation:
[
X_M(T) = 1-\exp\big(-\alpha,(M_s-T)\big)\quad\text{for } T<M_s,
]
or the simpler KM linearized exponential form:
[
X_M = 1-\exp[-\beta(M_s-T)],
]
with parameters fitted to alloy chemistry. KM gives martensite fraction based on undercooling below (M_s). ([Semantic Scholar][5])

Local phase fractions update material stiffness, yield strength, thermal properties, and latent heat effects (include latent heat during phase change, e.g. as source term in thermal PDE).

---

## 4 — Contact / interface resistance modelling (mathematical forms)

Contact resistance dominates heat generation in ERW. Mathematical modeling choices:

1. **Lumped surface resistance (R_c) (per unit area)**
   Surface current density jump:
   [
   q_c(x,t) = \frac{\big(\Delta\phi(x,t)\big)^2}{R_c(x,t)} = I(x,t)^2,R_c(x,t)
   ]
   with (R_c) modeled empirical function:
   [
   R_c \approx \frac{\rho_c}{A_r},\qquad A_r\propto\frac{F_n}{H(T)}
   ]
   where (F_n) is local normal force, (H(T)) hardness (temperature dependent), and (\rho_c) an interface resistivity — this yields (R_c\propto \rho_c H/F_n). See contact reviews. ([SpringerLink][3])

2. **Asperity / Holm model (micromechanical)**
   For contacts of many asperities, model contact spots as circular constrictions with Holm radius (a); constriction resistance per spot:
   [
   R_{\rm spot} \approx \frac{\rho}{2a},
   ]
   and total (R_c = \sum R_{\rm spot}^{-1}) reciprocity. This links mechanical deformation to electrical resistance.

3. **Temperature and melting**
   When local temperature reaches melting, contact resistance drops (liquid metal conduction) and mass flow/expulsion may occur; model transition with a switching function or phase field.

---

## 5 — Boundary / initial conditions (typical)

* Initial temperature (T(\mathbf{x},0)=T_0) (ambient).
* Electrical: total current (I(t)) at rollers; outer pipe surface electrically insulating.
* Thermal convection on pipe outer surface ( -k\partial_n T = h(T-T_\infty)). Radiation if temperatures high.
* Mechanical: pipe supports / clamping and rolling force (p(t)) on seam. Symmetry at axis for axisymmetric models.

---

## 6 — Dimensionless form and key nondimensional numbers

Non-dimensionalization helps identify regimes:

Let characteristic length (L) (pipe thickness or source width), time (t_c=L^2/\alpha) (diffusive time), temperature ( \Delta T = P/(kL)).

Define Peclet number for moving source (advection vs diffusion in moving frame):
[
Pe = \frac{vL}{\alpha}.
]
If (Pe\ll1) diffusion dominates (wide heat diffusion), if (Pe\gg1) advection (moving source) dominates and the thermal field is highly localized near the source.

Electrical thermal coupling strength: ratio of Joule heating to conductive cooling:
[
\Lambda = \frac{\sigma_e E^2,L^2}{k\Delta T}.
]

---

## 7 — Analytical / semi-analytical approximations (useful for checks)

* **Rosenthal / moving source solutions**: closed-form expressions exist for idealized geometries (point or line moving heat source in semi-infinite medium or thin plate). Use these for first estimates of peak temperatures and weld pool dimensions; they are the canonical checks for numerical models. ([ScienceDirect][1])

* **1D moving Gaussian model:** represent the moving seam as a time-dependent source in 1D:
  [
  \rho c_p \frac{\partial T}{\partial t} = k\frac{\partial^2 T}{\partial x^2} + \frac{P}{\sqrt{2\pi}\sigma}\exp!\Big(-\frac{(x-vt)^2}{2\sigma^2}\Big).
  ]
  This admits efficient semi-implicit numerical solution (Crank–Nicolson) and is excellent for generating cooling rates.

---

## 8 — Numerical solution strategy (recommended)

### Option A — Staggered (partitioned) scheme (practical)

1. Solve electrical problem for (\phi^n) with (\sigma_e(T^{n})) → compute (Q_{\rm Joule}^n).
2. Solve thermal PDE for (T^{n+1}) using implicit time integration (backward Euler or Crank–Nicolson).
3. Update mechanical problem (quasi-static) with thermal strains using (T^{n+1}) → compute contact pressure (p^{n+1}) and update (R_c^{n+1}).
4. Update metallurgical state (phase fractions) using thermal history at integration points → update material properties for next step.
5. Iterate inner loop until convergence (if strong coupling desired).

This is robust and easier to implement using existing FEM solvers (COMSOL/ANSYS/ABAQUS with user subroutines).

### Option B — Fully coupled (monolithic)

Assemble global residual of electro-thermo-mechanical system and solve with Newton–Raphson. Higher accuracy and stability at the cost of complexity and memory. Use for strongly coupled regimes (rapid melting and mechanical collapse).

### Discretization notes

* Use FEM with higher mesh density near seam (mesh grading, adaptive refinement). For 3D, prism/tetra elements near seam.
* Use implicit time integration for thermal (stiff); adaptive timestep controlled by max temperature change or Courant type criteria with moving source.
* For phase kinetics under non-isothermal conditions integrate JMAK incrementally using local time history (small substeps inside thermal step if necessary).

---

## 9 — Discretized example — 1D Crank–Nicolson (illustrative)

Discretize (\rho c_p \partial_t T = k\partial_{xx}T + Q(x,t)) on grid (x_i) with step (\Delta x) and timestep (\Delta t). Crank–Nicolson gives:
[
\rho c_p\frac{T_i^{n+1}-T_i^n}{\Delta t}
= \frac{k}{2}\left(\frac{T_{i+1}^{n+1}-2T_i^{n+1}+T_{i-1}^{n+1}}{\Delta x^2}

* \frac{T_{i+1}^{n}-2T_i^{n}+T_{i-1}^{n}}{\Delta x^2}\right) + \frac{Q_i^{n+1}+Q_i^{n}}{2}.
  ]
  Assemble tridiagonal system (A T^{n+1} = B T^n + S). (This is the practical algorithm used in the demo earlier.)

---

## 10 — Parameter estimation & calibration

* Unknowns: contact resistivity (\rho_c), functional dependence (R_c(T,p)), real contact area model constants, fraction of plastic work converted to heat (\beta), exact current waveform (I(t)).
* Use experimental thermocouple/IR seam temperature traces and metallurgical (microhardness, phase fraction) measurements to define an inverse problem:
  [
  \min_{\theta};\sum_j | T_{\rm sim}(x_j,t;\theta)-T_{\rm meas}(x_j,t)|^2 + \text{regularization}
  ]
  Solve with gradient-based (adjoint) or derivative-free optimization (if adjoint not available). Adjoint methods are efficient for many parameters but require full solver differentiation.

---

## 11 — Model outputs & diagnostics

* Time histories (T(\mathbf{x},t)) at critical points → cooling rates (\dot T) and (t_{8/5}) commonly used.
* Phase fraction maps (martensite, bainite, ferrite, pearlite).
* Residual stress and distortion fields from thermo-mechanical solve.
* Seam power density and cumulative energy delivered.
* Sensitivity maps (how seam quality changes with (I), (v), (p), (R_c)).

---

## 12 — Validation & verification plan

1. Verify heat solver against Rosenthal analytical / semi-analytical solutions (moving source) for simple geometries. ([ScienceDirect][1])
2. Validate contact resistance model with spot measurements or literature contact resistance vs. pressure curves. ([SpringerLink][3])
3. Validate phase predictions (martensite fraction, hardness) against metallography and hardness tests for known cooling curves; calibrate KM/JMAK parameters. ([Semantic Scholar][5])
4. For HF-ERW, compare predicted seam defects/toughness with published HF-ERW studies. ([ScienceDirect][2])

---

## 13 — Practical implementation checklist (step-by-step)

1. **Select geometry**: 2D axisymmetric for pipe wall + local 3D patch at seam.
2. **Mesh**: refine at seam; use boundary layer elements through thickness.
3. **Material data**: collect (k(T),c_p(T),\rho(T),\sigma_e(T),H(T)) and phase kinetics (JMAK/KM) parameters.
4. **Set electrical BCs**: total applied current waveform; initial (R_c) guess.
5. **Solve**: staggered electro → thermal → mechanical → kinetics loop each time step. Use implicit thermal solver.
6. **Calibrate**: tune (R_c), contact model constants and power partition to match measured seam temperature and microstructure.
7. **Postprocess**: report peak temperatures, cooling rates, predicted HAZ phases, residual stresses, and risk zones (incomplete fusion, high hardness).

---

## 14 — Common pitfalls & recommended mitigations

* **Neglecting temperature dependence** of (\sigma_e) and (k): leads to wrong heat localization. Always include T-dependence.
* **Poor mesh near contact**: underestimates peak temperatures; use local refinement and possibly adaptive remeshing.
* **Not capturing contact evolution**: treat (R_c) as constant only for rough estimates; for fidelity model (R_c(T,p)).

---

## 15 — Recommended references (selected, for model building and verification)

* Rosenthal, P. “The theory of moving heat sources” — classic analytical solutions for moving heat sources (see engineering references on the Rosenthal solution). ([ScienceDirect][1])
* Hamedi et al., review of electrical contact resistance in resistance welding — critical for (R_c) modeling and literature overview. ([SpringerLink][3])
* Koistinen & Marburger (empirical martensite relation) — for martensite fraction modeling. ([Semantic Scholar][5])
* Hart-Rawung et al. / recent unified JMAK papers — for non-isothermal continuous cooling phase kinetics. ([ScienceDirect][4])
* Ravikiran K., “A critical review on high-frequency ERW” — process specifics for HF-ERW and recent improvements. ([ScienceDirect][2])

(If you want, I can assemble a full bibliography with direct links and short notes on each paper — tell me if you prefer PDF copies or DOIs.)

---

## 16 — Deliverables I can produce for you now (examples)

* Full ready-to-run FEM/FEA recipe for COMSOL or ANSYS (geometry, mesh, PDE modules, solver sequence, exemplar BC values).
* A 2D axisymmetric Python/FEniCS or finite-difference code that solves the coupled electro-thermal problem with a contact resistance model and outputs cooling curves for the pipe wall.
* Phase-kinetics coupling (JMAK + KM) implemented and validated on typical carbon steel cooling histories.

Tell me which one you want and I’ll implement it (code, step-by-step COMSOL recipe, or both) right away.

---

### Quick summary (one paragraph)

Model ERW by solving the coupled quasi-static electrical conduction (to compute Joule heating), transient heat conduction (with temperature-dependent properties and moving seam source), quasi-static thermo-elastic-plastic mechanics (to get contact pressure and residual stress), and phase-transformation kinetics (JMAK/KM) to predict microstructure. Contact resistance (R_c), which links mechanics and electrical heating, is the most sensitive parameter and must be modeled as a function of pressure and temperature and calibrated experimentally. Use staggered implicit schemes for robust, practical simulation; verify against Rosenthal analytical solutions and literature contact-resistance studies. ([ScienceDirect][1])

---

If you’d like, I’ll now:

* produce a **complete FEM recipe for COMSOL** (materials, BCs, mesh sizes, solver settings) **or**
* generate **Python (FEniCS or finite-difference) code** for a 2D axisymmetric electro-thermal model with contact resistance and phase-kinetics coupling,

— pick one and I’ll do it immediately.

[1]: https://www.sciencedirect.com/topics/engineering/rosenthal-solution?utm_source=chatgpt.com "Rosenthal Solution - an overview"
[2]: https://www.sciencedirect.com/science/article/pii/S1526612524006261?utm_source=chatgpt.com "A critical review on high-frequency electric-resistance ..."
[3]: https://link.springer.com/article/10.1007/s40194-016-0419-4?utm_source=chatgpt.com "A review of electrical contact resistance modeling in ..."
[4]: https://www.sciencedirect.com/science/article/pii/S0924013623000018?utm_source=chatgpt.com "A unified model for isothermal and non-isothermal phase ..."
[5]: https://www.semanticscholar.org/paper/A-general-equation-prescribing-the-extent-of-the-in-Koistinen-Marburger/b0740afaf8feeaa22a09629800b7133d5aaef8be?utm_source=chatgpt.com "A general equation prescribing the extent of the austenite ..."
