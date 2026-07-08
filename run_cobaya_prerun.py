import os
from cobaya.run import run

# Pre-run breve per calibrare la proposal del run di produzione
# (run_cobaya_stratoverso.py). Stessa configurazione (likelihood, parametri
# fissi/liberi, covmat iniziale a mano in covmats/stratoverso_initial.covmat),
# ma con un tetto basso di campioni e convergenza non richiesta: lo scopo
# e' solo accumulare un numero di passi accettati sufficiente a far
# imparare a Cobaya una covmat empirica (scritta automaticamente in
# chains/stratoverso_prerun.covmat ad ogni checkpoint), da usare poi come
# covmat iniziale del run di produzione vero. learn_every e' abbassato
# rispetto al default (40d) per far scattare il primo apprendimento/
# checkpoint dentro la finestra breve di questo pre-run.
#
# 2026-06-24, v2 (prior allargati): il primo pre-run (prior H0 in [60,75],
# z_trans in [5,50]) si era bloccato esattamente sui due bordi inferiori,
# con il chi2 ancora in discesa monotona (42189 -> 3402, -92%) -- confermato
# NON essere un bug: a quel punto 100*theta_s dello Stratoverso (1.0447) e'
# molto piu' vicino al valore Planck (1.0411) del LCDM puro alla stessa
# (H0, omega_b, omega_cdm) (1.0091), prova diretta della degenerazione
# geometria/energia oscura modificata (vedi STATO_LAVORO.md). Prior
# allargati qui (H0 in [50,80], z_trans in [0.1,50]) per mappare la
# degenerazione senza che i bordi tagliuzzino la discesa, prima di
# costruire qualsiasi covmat empirica.
info = {
    "packages_path": "/Users/coldmac/.cobaya/packages",
    "theory": {
        "classy": {
            "path": "/Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso",
            "extra_args": {
                "Omega_scf": 0.1,
                "attractor_ic_scf": "yes",
                "scf_parameters": "10.0, 0.0, 0.0, 0.0",
                "scf_tuning_index": 0
            }
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
        "H0": {
            "prior": {"min": 50.0, "max": 80.0},
            "ref": 67.4,
            "proposal": 0.3,
            "latex": r"H_0"
        },
        "omega_b": 0.02237,
        "omega_cdm": {
            "prior": {"min": 0.10, "max": 0.14},
            "ref": 0.1200,
            "proposal": 0.001,
            "latex": r"\omega_{cdm}"
        },
        "tau_reio": 0.0544,
        "A_s": {
            "prior": {"min": 1.5e-9, "max": 2.8e-9},
            "ref": 2.1e-9,
            "proposal": 5.0e-11,
            "latex": r"A_s"
        },
        "n_s": 0.9649,
        "A_planck": {
            "prior": {"dist": "norm", "loc": 1.0, "scale": 0.0025},
            "ref": 1.0,
            "proposal": 0.0005,
            "latex": r"y_{\rm cal}"
        },
        "age": {
            "latex": r"t_0"
        },
        "lambda_reset": {
            "prior": {"min": 0.25, "max": 0.35},
            "ref": 0.300,
            "proposal": 0.005,
            "latex": r"\lambda"
        },
        "g_holographic": {
            "prior": {"min": 0.005, "max": 0.025},
            "ref": 0.014,
            "proposal": 0.001,
            "latex": r"g"
        },
        "phi_phase": {
            "prior": {"min": 0.0, "max": 6.28318},
            "ref": 3.14,
            "proposal": 0.1,
            "latex": r"\varphi"
        },
        "z_trans": {
            "prior": {"min": 0.1, "max": 50.0},
            "ref": 20.0,
            "proposal": 2.0,
            "latex": r"z_{\rm trans}"
        },
        "delta_z": {
            "prior": {"min": 1.0, "max": 15.0},
            "ref": 5.0,
            "proposal": 0.5,
            "latex": r"\Delta z"
        }
    },
    "sampler": {
        "mcmc": {
            "max_samples": 300,
            "Rminus1_stop": 0.3,
            "max_tries": 1000,
            "learn_every": "10d",
            "drag": False,
            "covmat": "covmats/stratoverso_initial.covmat",
        }
    },
    "output": "chains/stratoverso_prerun_wide",
    "resume": True,
    "stop_at_error": False,
}

os.makedirs("chains", exist_ok=True)

if __name__ == "__main__":
    updated_info, sampler = run(info)
    print("Pre-run completato. Covmat empirica in chains/stratoverso_prerun_wide.covmat")
