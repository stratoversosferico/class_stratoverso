import numpy as np
from classy import Class

STRAT_PARAMS = {
    "H0": 67.4, "omega_b": 0.02237, "omega_cdm": 0.1200, "Omega_scf": 0.1,
    "attractor_ic_scf": "yes", "scf_parameters": "10.0, 0.0, 0.0, 0.0",
    "scf_tuning_index": 0, "lambda_reset": 0.300, "g_holographic": 0.014,
    "phi_phase": 3.14, "output": "",
}

cosmo = Class()
cosmo.set(STRAT_PARAMS)
cosmo.compute()

z_list = sorted(list(np.arange(0.0, 3.01, 0.1)), reverse=True)
H = np.array([cosmo.Hubble(z) for z in z_list])
print(f"{'z':>6} {'H_strat [1/Mpc]':>18} {'dH/dz (numeric)':>18} {'d2H/dz2 (numeric)':>20}")
z_arr = np.array(sorted(z_list))
H_arr = np.array([cosmo.Hubble(z) for z in z_arr])
dH = np.gradient(H_arr, z_arr)
d2H = np.gradient(dH, z_arr)
for z, h, d1, d2 in zip(z_arr, H_arr, dH, d2H):
    print(f"{z:6.2f} {h:18.10e} {d1:18.6e} {d2:20.6e}")
cosmo.struct_cleanup()
cosmo.empty()
