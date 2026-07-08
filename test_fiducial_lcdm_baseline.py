import os
from cobaya.run import run

PACKAGES_PATH = "/Users/coldmac/.cobaya/packages"
CLASS_PATH = "/Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso"

info = {
    "packages_path": PACKAGES_PATH,
    "theory": {
        "classy": {
            "path": CLASS_PATH,
            "extra_args": {},
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
        "H0": 67.4,
        "omega_b": 0.02237,
        "omega_cdm": 0.1200,
        "tau_reio": 0.0544,
        "A_s": 2.1e-9,
        "n_s": 0.9649,
        "A_planck": 1.0,
        "age": {"latex": r"t_0"},
    },
    "sampler": {"evaluate": {}},
    "output": "test_logs/fiducial_eval/lcdm_baseline",
    "force": True,
    "stop_at_error": False,
}

if __name__ == "__main__":
    os.makedirs("test_logs/fiducial_eval", exist_ok=True)
    updated_info, sampler = run(info)
    products = sampler.products()
    sample = products["sample"]
    row = sample.data.iloc[0]
    print("\n=== Baseline LCDM (has_scf off), stesso H0/omega_b/omega_cdm/A_s/n_s/tau_reio ===")
    print(f"age (Gyr)      = {row.get('age', float('nan')):.6f}")
    print(f"chi2 totale    = {row['chi2']:.4f}")
    for col in sample.data.columns:
        if col.startswith("chi2__"):
            print(f"  {col[len('chi2__'):]:45s} = {row[col]:.4f}")
