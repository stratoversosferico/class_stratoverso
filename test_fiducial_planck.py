"""
Valutazione del modello Stratoverso al punto fiduciale
(H0=67.4, lambda_reset=0.300) contro le likelihood reali:
  - Planck 2018: low-l TT + low-l EE + high-l plik_lite TTTEEE (clipy)
  - DESI DR2 BAO (tutti i tracciatori)
  - Pantheon+ (SNIa)

Usa il sampler "evaluate" di Cobaya: una singola valutazione del
modello al punto dato, niente catena MCMC.
"""

import os
from cobaya.run import run

PACKAGES_PATH = "/Users/coldmac/.cobaya/packages"
CLASS_PATH = "/Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso"

info = {
    "packages_path": PACKAGES_PATH,
    "theory": {
        "classy": {
            "path": CLASS_PATH,
            "extra_args": {
                "Omega_scf": 0.1,
                "attractor_ic_scf": "yes",
                "scf_parameters": "10.0, 0.0, 0.0, 0.0",
                "scf_tuning_index": 0,
            },
        }
    },
    "likelihood": {
        "planck_2018_lowl.TT_clik": {},
        "planck_2018_lowl.EE_clik": {},
        "planck_2018_highl_plik.TTTEEE_lite": {},
        "planck_2018_lensing.clik": {},
        "bao.desi_dr2.desi_bao_all": {},
        "sn.pantheonplus": {},
    },
    "params": {
        # Punto fiduciale richiesto
        "H0": 67.4,
        "lambda_reset": 0.300,
        # Parametri cosmologici standard (Planck 2018 TT,TE,EE+lowE+lensing best fit)
        "omega_b": 0.02237,
        "omega_cdm": 0.1200,
        "tau_reio": 0.0544,
        "A_s": 2.1e-9,
        "n_s": 0.9649,
        # Parametri Stratoverso non specificati dall'utente: default usati nei test precedenti
        "g_holographic": 0.014,
        "phi_phase": 3.14,
        # Calibrazione Planck (nessun offset assunto)
        "A_planck": 1.0,
        # Derivati utili da riportare
        "age": {"latex": r"t_0"},
    },
    "sampler": {
        "evaluate": {}
    },
    "output": "test_logs/fiducial_eval/fiducial",
    "force": True,
    "stop_at_error": False,
}

if __name__ == "__main__":
    os.makedirs("test_logs/fiducial_eval", exist_ok=True)
    updated_info, sampler = run(info)

    products = sampler.products()
    sample = products["sample"]
    row = sample.data.iloc[0]

    print("\n=== Punto fiduciale: H0=67.4, lambda_reset=0.300 ===")
    print(f"age (Gyr)      = {row.get('age', float('nan')):.6f}")
    print(f"chi2 totale    = {row['chi2']:.4f}")
    print("--- contributi per likelihood ---")
    for col in sample.data.columns:
        if col.startswith("chi2__"):
            print(f"  {col[len('chi2__'):]:45s} = {row[col]:.4f}")

    planck_cols = [c for c in sample.data.columns
                   if c.startswith("chi2__planck")]
    chi2_planck = sum(row[c] for c in planck_cols)
    print(f"\nchi2 Planck (somma low-l TT+EE, plik_lite, lensing) = {chi2_planck:.4f}")
