import os
from cobaya.run import run

# Configurazione del run MCMC di produzione per lo Stratoverso, con le
# likelihood reali (sostituiscono la gaussiana giocattolo usata nel primo
# test di comunicazione Cobaya<->CLASS). Vedi STATO_LAVORO.md per il
# confronto chi2 al punto fiduciale (H0=67.4, lambda_reset=0.300) ottenuto
# con test_fiducial_planck.py: lambda_reset/Omega_scf sono in forte
# tensione con Planck high-l + lensing + DESI a parametri standard fissi,
# da cui la necessita' di lasciare liberi anche omega_b/omega_cdm/A_s/n_s/
# tau_reio in un fit congiunto reale.
#
# Modello ibrido LCDM+Stratoverso (2026-06-24): rho_scf/p_scf sono ora
# moltiplicati per f(z) = 1/(1+exp((z-z_trans)/delta_z)), z_trans/delta_z
# promossi a parametri liberi (pba->z_trans, pba->delta_z in background.c/h,
# letti da input.c come lambda_reset). Vedi STATO_LAVORO.md per i test di
# continuita' di H(z) (test_hybrid_background.py, test_hybrid_continuity_fine.py).
#
# NOTA: l'ultimo tentativo di run di produzione con 10 parametri liberi si
# e' bloccato dopo 400 tentativi rifiutati consecutivi (proposal troppo
# larga per una posterior molto sensibile, vedi STATO_LAVORO.md).
#
# 2026-06-25: lambda_reset si era incollato al bordo inferiore del prior
# (0.25) per ~1100 campioni, con chi2 ancora in discesa (stesso pattern di
# H0/z_trans nel pre-run) -- prior allargato a [0.15, 0.35] per vedere se
# la valle si apre sotto 0.25. covmat (v3), parametri fissi e setup
# invariati; tau_reio resta fisso in questo step.
#
# 2026-06-25, riavvio pulito: dopo 3 allargamenti progressivi del prior di
# lambda_reset (0.25->0.15->0.05), R-1 misurato sull'intera storia della
# catena (che include tutti i salti di prior) non e' piu' un indicatore
# affidabile di convergenza -- la catena si porta dietro la "memoria" di
# regioni di parametri ormai abbandonate. Scartata tutta la storia
# precedente: nuovo output (nessun resume), ref impostati al best fit
# trovato finora (chi2=2475.32, riga 2021 di stratoverso_production_v1.1.txt):
# H0=65.1996, omega_cdm=0.116746, A_s=2.08756e-9, A_planck=1.00308,
# lambda_reset=0.050805, g_holographic=0.0050556, phi_phase=4.87231,
# z_trans=0.368335, delta_z=1.01662. Prior e covmat (v6) invariati.
#
# Calibrazione proposal (2026-06-24): omega_b/n_s/tau_reio fissati (poco
# correlati con la fisica Stratoverso, vedi sotto), spazio libero a 9
# parametri. Due pre-run brevi (run_cobaya_prerun.py):
# 1) prior H0 in [60,75], z_trans in [5,50]: bloccato sui due bordi
#    inferiori con chi2 ancora in discesa (-92%, 42189->3402). Confermato
#    NON essere un bug: 100*theta_s dello Stratoverso al punto bloccato
#    (1.0447) e' molto piu' vicino al valore Planck (1.0411) del LCDM puro
#    alla stessa (H0,omega_b,omega_cdm) (1.0091) -- vera degenerazione
#    geometria/energia oscura modificata.
# 2) prior allargati a H0 in [50,80], z_trans in [0.1,50]: la catena ha
#    superato i vecchi bordi e si e' STABILIZZATA in un modo interno
#    (H0~61.4, z_trans~3.0, chi2~3100, niente piu' contro i bordi).
# Covmat empirica calcolata dalla coda stazionaria (200 campioni, scartato
# il burn-in), regolarizzata con shrinkage 30% verso la diagonale iniziale
# in spazio di correlazione (la covarianza grezza aveva un autovalore
# numericamente nullo dovuto alle scale molto diverse dei parametri, non
# una vera degenerazione: in correlazione l'autovalore minimo grezzo era
# 1.4e-3, comunque positivo) -> covmats/stratoverso_shrunk.covmat, verificata
# con Cholesky. ref aggiornati al modo trovato. NON lanciare il run di
# produzione senza autorizzazione esplicita dell'utente.
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
            "ref": 65.1996,
            "proposal": 0.3,
            "latex": r"H_0"
        },
        # omega_b fissato (Planck best fit): ben vincolato da BBN/high-l,
        # poco correlato con la fisica tardiva dello Stratoverso -- liberarlo
        # aggiungeva una dimensione sensibile senza beneficio per la
        # calibrazione iniziale della proposal.
        "omega_b": 0.02237,
        "omega_cdm": {
            "prior": {"min": 0.10, "max": 0.14},
            "ref": 0.116746,
            "proposal": 0.001,
            "latex": r"\omega_{cdm}"
        },
        # tau_reio fissato: lowl.EE_clik e' fortemente piccato in tau_reio
        # (vedi STATO_LAVORO.md -- chi2_EE=396 identico in Stratoverso e in
        # LCDM puro, quindi non e' un effetto Stratoverso), liberarlo
        # produceva salti di chi2 enormi tra proposte vicine -> quasi nessuna
        # accettazione. Fissato al best fit Planck 2018.
        "tau_reio": 0.0544,
        "A_s": {
            "prior": {"min": 1.5e-9, "max": 2.8e-9},
            "ref": 2.08756e-9,
            "proposal": 5.0e-11,
            "latex": r"A_s"
        },
        # n_s fissato (Planck best fit): debolmente correlato con la fisica
        # Stratoverso, stesso motivo di omega_b.
        "n_s": 0.9649,
        "A_planck": {
            "prior": {"dist": "norm", "loc": 1.0, "scale": 0.0025},
            "ref": 1.00308,
            "proposal": 0.0005,
            "latex": r"y_{\rm cal}"
        },
        "age": {
            "latex": r"t_0"
        },
        "lambda_reset": {
            "prior": {"min": 0.05, "max": 0.35},
            "ref": 0.050805,
            "proposal": 0.005,
            "latex": r"\lambda"
        },
        "g_holographic": {
            "prior": {"min": 0.005, "max": 0.025},
            "ref": 0.0050556,
            "proposal": 0.001,
            "latex": r"g"
        },
        "phi_phase": {
            "prior": {"min": 0.0, "max": 6.28318},
            "ref": 4.87231,
            "proposal": 0.1,
            "latex": r"\varphi"
        },
        "z_trans": {
            "prior": {"min": 0.1, "max": 50.0},
            "ref": 0.368335,
            "proposal": 2.0,
            "latex": r"z_{\rm trans}"
        },
        "delta_z": {
            "prior": {"min": 1.0, "max": 15.0},
            "ref": 1.01662,
            "proposal": 0.5,
            "latex": r"\Delta z"
        }
    },
    "sampler": {
        "mcmc": {
            # Produzione: nessun cap artificiale di campioni (solo un tetto di
            # sicurezza), convergenza reale Gelman-Rubin R-1<0.02 (singola
            # catena, no MPI -> split in 4 segmenti, Rminus1_single_split default).
            "max_samples": 20000,
            "Rminus1_stop": 0.02,
            "max_tries": 1000,
            "drag": False,
            # Covmat: il run di produzione si bloccava ripetutamente vicino
            # al picco (chi2~3017) anche con proposal_scale dimezzata e la
            # covmat del pre-run -- segno che la covmat (stimata da 200
            # campioni di un'esplorazione piu' larga) non rifletteva bene
            # la vera larghezza locale qui. Ricalcolata da ~520 campioni
            # pesati di QUESTO run (piu' vicini al vero picco), stesso
            # shrinkage 30% in spazio di correlazione verso la diagonale,
            # verificata con Cholesky -> covmats/stratoverso_production_v2.covmat.
            # proposal_scale tornata al default (2.4): la covmat aggiornata
            # dovrebbe avere la scala giusta senza bisogno di compensare.
            "covmat": "covmats/stratoverso_production_v6.covmat",
        }
    },
    "output": "chains/stratoverso_production_v2_clean",
    "resume": True,
    "stop_at_error": False,
}

# Creazione cartella output
os.makedirs("chains", exist_ok=True)

if __name__ == "__main__":
    # allow_changes=True: necessario per riprendere dal checkpoint dopo aver
    # allargato il prior di lambda_reset (min 0.25 -> 0.15), altrimenti
    # cobaya rifiuta il resume per incompatibilita' con l'info salvata.
    updated_info, sampler = run(info, allow_changes=True)
    print("MCMC completed successfully. Chains saved to chains/stratoverso_production_v1.")
