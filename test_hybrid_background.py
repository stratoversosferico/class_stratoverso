"""
Passo 3 del piano ibrido LCDM+Stratoverso: verifica che H(z) sia continua
e che lo Stratoverso si attivi/disattivi correttamente tramite f(z)
(z_trans=20, delta_z=5, hardcoded in background.c per ora).

Stampa H(z) su una griglia che copre sia i punti richiesti (z=100,20,2,0)
sia un campionamento fitto attorno a z_trans=20 per controllare la
continuita', confrontando col background LCDM puro (has_scf=False) agli
stessi parametri standard.
"""

import numpy as np
from classy import Class


def f_transition(z, z_trans=20.0, delta_z=5.0):
    return 1.0 / (1.0 + np.exp((z - z_trans) / delta_z))


STRAT_PARAMS = {
    "H0": 67.4,
    "omega_b": 0.02237,
    "omega_cdm": 0.1200,
    "Omega_scf": 0.1,
    "attractor_ic_scf": "yes",
    "scf_parameters": "10.0, 0.0, 0.0, 0.0",
    "scf_tuning_index": 0,
    "lambda_reset": 0.300,
    "g_holographic": 0.014,
    "phi_phase": 3.14,
    "output": "",
}

LCDM_PARAMS = {
    "H0": 67.4,
    "omega_b": 0.02237,
    "omega_cdm": 0.1200,
    "output": "",
}


def get_H_of_z(params, z_list):
    cosmo = Class()
    cosmo.set(params)
    cosmo.compute()
    H = np.array([cosmo.Hubble(z) for z in z_list])
    age = cosmo.age()
    cosmo.struct_cleanup()
    cosmo.empty()
    return H, age


if __name__ == "__main__":
    # punti richiesti + campionamento fitto attorno a z_trans=20
    z_main = [100.0, 50.0, 20.0, 2.0, 0.0]
    z_fine = list(np.arange(10.0, 31.0, 1.0))
    z_list = sorted(set(z_main + z_fine), reverse=True)

    H_strat, age_strat = get_H_of_z(STRAT_PARAMS, z_list)
    H_lcdm, age_lcdm = get_H_of_z(LCDM_PARAMS, z_list)

    print(f"age Stratoverso = {age_strat:.6f} Gyr")
    print(f"age LCDM puro   = {age_lcdm:.6f} Gyr\n")

    print(f"{'z':>8} {'f(z)':>8} {'H_strat [1/Mpc]':>18} {'H_lcdm [1/Mpc]':>18} {'rel.diff':>12}")
    for z, Hs, Hl in zip(z_list, H_strat, H_lcdm):
        fz = f_transition(z)
        reldiff = (Hs - Hl) / Hl
        flag = "  <-- z_trans" if z == 20.0 else ""
        print(f"{z:8.1f} {fz:8.4f} {Hs:18.10e} {Hl:18.10e} {reldiff:12.3e}{flag}")

    # continuita': differenza finita di H_strat-H_lcdm attorno a z_trans,
    # deve variare con continuita' (nessun salto) man mano che z attraversa 20
    print("\n--- verifica continuita' (rel.diff = (H_strat-H_lcdm)/H_lcdm) intorno a z_trans=20 ---")
    idx_sorted = np.argsort(z_list)
    z_arr = np.array(z_list)[idx_sorted]
    reldiff_arr = (H_strat[idx_sorted] - H_lcdm[idx_sorted]) / H_lcdm[idx_sorted]
    mask = (z_arr >= 10) & (z_arr <= 30)
    for z, rd in zip(z_arr[mask], reldiff_arr[mask]):
        print(f"  z={z:5.1f}  rel.diff={rd:12.3e}  f(z)={f_transition(z):.4f}")
