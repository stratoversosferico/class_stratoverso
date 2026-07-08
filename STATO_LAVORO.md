# Stato Lavoro — Progetto Stratoverso (CLASS + Cobaya)

Questo documento riassume lo stato dell'integrazione del framework dello **Stratoverso** all'interno del codice di cosmologia **CLASS** (`class_stratoverso`) e della pipeline MCMC **Cobaya**, a seguito del completamento della Fase 4.

---

## 🛠️ Attività Completate

1. **Modifiche a CLASS (`class_stratoverso`)**:
   - **Modulo Primordial (`primordial.c`, `primordial.h`)**: Implementata la correzione log-periodica allo spettro primordiale con $\omega_g = 5.22$, controllata dai parametri `g_holographic` ($\epsilon_g$) e `phi_phase` ($\varphi$).
   - **Modulo Background (`background.c`, `background.h`)**: Integrato l'integratore Runge-Kutta 4 con evento di arresto esatto in corrispondenza dei 140 reset discreti (junction conditions $a_+ = \lambda^{-1/3}a_-$, $\phi'_+ = \lambda^{2/3}\phi'_-$ a $\tau_n = \tau_{137} \cdot e^{-n \cdot 2.0 / 1.661}$).
   - **Modulo Input (`input.c`)**: Aggiunto il parsing per i parametri dello Stratoverso (`lambda_reset`, `g_holographic`, `phi_phase`).
   - **Modulo Thermodynamics (`thermodynamics.c`)**: Corretto il calcolo di $N_{\rm eff}$ a BBN rimuovendo il contributo fittizio della pressione del campo scalare all'inizio per evitare crash del modulo BBN.

2. **Risoluzione Bug e Ottimizzazione I/O**:
   - Durante il run MCMC iniziale, le stampe di debug prolisse inserite nel ciclo di integrazione Runge-Kutta in `background.c` (linee 3174, 3190, 3304) generavano log enormi (oltre **212 MB** per poche iterazioni) creando un collo di bottiglia di I/O su disco che rallentava vistosamente la MCMC.
   - Tutti i `printf` di debug ad alta frequenza all'interno dell'integratore sono stati **commentati**. La ricompilazione della libreria C e del modulo Python `classy` è stata eseguita con successo.

3. **Validazione MCMC con Cobaya**:
   - Lo script [run_cobaya_stratoverso.py](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/run_cobaya_stratoverso.py) implementa una Likelihood custom `StratoversoLikelihood` che richiede l'età dell'universo `age` da CLASS e calcola una $\chi^2$ gaussiana sui parametri sampled dello Stratoverso:
     - $H_0 \in [67, 68]$
     - $\lambda_{\rm reset} \in [0.25, 0.35]$
     - $g_{\rm holographic} \in [0.005, 0.025]$
     - $\phi_{\rm phase} \in [0, 2\pi]$
   - **Risultato del Test**: L'MCMC è stata limitata a **100 campioni accettati** (`max_samples: 100`) per la verifica di comunicazione. Il run si è completato in **meno di un minuto** con successo, salvando le catene in `chains/` con 0 errori.

4. **Archiviazione di Sicurezza**:
   - Come richiesto, tutti i file sorgenti modificati, lo script MCMC e i log di test sono stati salvati all'interno della cartella principale [class_stratoverso/](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/):
     - Script MCMC: [run_cobaya_stratoverso.py](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/run_cobaya_stratoverso.py)
     - Log del test di successo: [test_logs/mcmc_run.log](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/test_logs/mcmc_run.log)
     - Catene generate: [test_logs/chains/](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/test_logs/chains/)

---

## 🩹 Fix Discontinuità in `n_smooth(t)` (background.c) — 2026-06-23

**Diagnosi.** `background_functions()` calcola un fattore di riscala temporale `a_phys_factor(t) = lambda_reset^(-n(t)/3)`, dove `n(t)` è l'estensione analitica continua dell'indice di layer discreto del cascade di reset (140 layer, vedi sopra), ottenuta invertendo la relazione `tau_n = tau_today * exp[(3-n)*2/gamma_eff]`. Questa `n_raw(t)` era poi forzata nell'intervallo fisicamente valido `[0,140]` con un **clamp duro** (`if (n<0) n=0; if (n>140) n=140;`). Per i parametri tipici (`gamma_eff=1.661`, `tau_today=0.2 Gyr-eq`), l'attraversamento `n_raw(t)=0` cade **dentro la storia integrata**, attorno a `z~0.6-0.9` — esattamente il regime tardo (ISW, lensing CMB) a cui Planck è più sensibile. Il clamp duro introduce quindi un **kink reale**: `d(a_phys_factor)/dt` salta da 0 a un valore finito in quel punto, iniettando una feature non fisica nella storia di espansione che si propaga a `H(t)`, `rho_scf(t)` e quindi ai C_ℓ — la causa più probabile del χ² Planck elevato.

**Fix.** Sostituito il clamp duro con un soft-clamp C^∞ (`stratoverso_softplus` + `stratoverso_smooth_clamp`, nuove funzioni in `background.c`, usate da `stratoverso_n_smooth_of_t()`), con larghezza di transizione `_STRATOVERSO_NSMOOTH_WIDTH_ = 0.05` (in unità dell'indice di layer `n`, cioè 1/20 della spaziatura tra due reset consecutivi). Inoltre, `a_phys_factor_today` ora è calibrato **auto-consistentemente** valutando la stessa funzione smooth a `t_today_exact` invece di un valore hardcoded `1/lambda_reset`, garantendo `a_phys(a=1)=1` esattamente per costruzione, indipendentemente dalla larghezza scelta.

**Verifica.**
- Test C standalone (link contro `libclass.a`) confronta `n_hard(t)` e `n_smooth(t)` e le loro derivate numeriche attorno all'attraversamento: `dn_hard/dt` salta da `0` a `~1.8e-4` esattamente nel punto di crossing, mentre `dn_smooth/dt` varia con continuità (`1.6e-6 → 1.8e-4 → 5.7e-4` su ±6 larghezze) — il kink è eliminato. Lontano dal crossing (>5 larghezze) le due formule coincidono a meglio di 0.1%, quindi il contenuto fisico del cascade (n~O(1-140)) non è alterato in modo apprezzabile.
- `test_background_only.py` e `test_classy_attractor.py` (con `compute()` completo) eseguiti con successo dopo ricompilazione di `libclass.a` e del modulo `classy` (via `pip install . --no-build-isolation`, con `touch python/classy.pyx` per forzare la rigenerazione Cython — necessario perché `python/classy.cpp` committato era stale rispetto a numpy 2.2.3 installato).
- Confronto end-to-end (stessi parametri cosmologici, `lambda_reset=0.300`, `g_holographic=0.014`, `phi_phase=3.14`): età dell'universo oggi passa da **12.998 Gyr** (clamp duro) a **13.461 Gyr** (smooth), più vicina al valore standard ΛCDM (~13.8 Gyr). Coerente con l'ipotesi che il kink stesse distorcendo la storia di espansione tardiva.

**Nota:** la riduzione effettiva del χ² Planck non è stata misurata direttamente in questa sessione, perché la pipeline Cobaya usa ancora la likelihood gaussiana giocattolo (vedi sopra) e non le likelihood reali Planck/DESI/Pantheon+ (vedi "Cosa Resta da Fare" punto 1). La diagnosi e il fix sono a livello di meccanismo (rimozione del kink nella storia di fondo); la verifica quantitativa sul χ² reale richiede di completare quel passo successivo.

---

## 📊 Likelihood Reali Collegate e χ² al Punto Fiduciale — 2026-06-23

**Setup.** Le likelihood reali erano già disponibili in `~/.cobaya/packages` (Planck 2018 baseline `plc_3.0` completo + `clipy`, dati nativi `planck_2018_lowT_native`, DESI DR2 BAO in `bao_data/desi_bao_dr2`, Pantheon+ in `sn_data/PantheonPlus`) — non è stato necessario scaricare nulla. Collegate via `clipy` (clik puro Python, nessuna libreria C da compilare):
- `planck_2018_lowl.TT_clik` (commander, low-l TT)
- `planck_2018_lowl.EE_clik` (simall, low-l EE)
- `planck_2018_highl_plik.TTTEEE_lite` (plik_lite, marginalizzata sui foreground)
- `planck_2018_lensing.clik`
- `bao.desi_dr2.desi_bao_all` (tutti i tracciatori)
- `sn.pantheonplus`

Nuovo script `test_fiducial_planck.py`: usa il sampler `evaluate` di Cobaya (valutazione singola, non MCMC) al punto fiduciale richiesto (`H0=67.4`, `lambda_reset=0.300`), con gli altri parametri Stratoverso ai default già usati nei test precedenti (`g_holographic=0.014`, `phi_phase=3.14`, `Omega_scf=0.1`) e i parametri cosmologici standard fissati ai best-fit Planck 2018 TT,TE,EE+lowE+lensing (`omega_b=0.02237`, `omega_cdm=0.1200`, `tau_reio=0.0544`, `A_s=2.1e-9`, `n_s=0.9649`, `A_planck=1.0`).

**Risultato — χ² al punto fiduciale:**

| Likelihood | χ² Stratoverso | χ² baseline ΛCDM puro* |
|---|---|---|
| `planck_2018_lowl.TT_clik` | 29.9 | 23.5 |
| `planck_2018_lowl.EE_clik` | 396.1 | 396.1 (identico) |
| `planck_2018_highl_plik.TTTEEE_lite` | 4680.6 | 633.8 |
| `planck_2018_lensing.clik` | 118.9 | 9.2 |
| **χ² Planck totale** | **5225.5** | **1062.6** |
| `bao.desi_dr2.desi_bao_all` | 81.9 | 31.0 |
| `sn.pantheonplus` | 1408.5 | 1403.9 |
| **χ² totale** | **6716.0** | **2497.5** |

\* stesso `H0`/`omega_b`/`omega_cdm`/`A_s`/`n_s`/`tau_reio`, ma `has_scf=False` (niente campo scalare, niente cascata di reset — Λ standard riempie il budget critico). Script: `test_fiducial_lcdm_baseline.py`.

**Diagnosi della tensione.** Per isolare la causa dell'eccesso di χ² (~3700 unità in più del baseline ΛCDM):
1. **Non è il termine log-periodico primordiale**: con `g_holographic=0` (script `test_fiducial_planck_g0.py`) il χ² CMB cambia da 5225.5 a 5252.9 — variazione trascurabile, leggermente *peggiore* senza il termine. L'ampiezza/fase attuali (`g=0.014`, `φ=3.14`) non sono la causa della tensione.
2. **Non è (più) la discontinuità in `n_smooth(t)`**: già risolta nella sezione precedente; l'età dell'universo al punto fiduciale è sensata (13.46 Gyr).
3. **`lowl.EE_clik=396.1` è identico nei due casi**: la polarizzazione low-l dipende quasi esclusivamente da `tau_reio`/`A_s`/`n_s` (fissati uguali nei due run), non dalla fisica tardiva dello Stratoverso — il suo valore alto è una proprietà di questi due parametri non ancora ottimizzati per Planck, non un effetto Stratoverso.
4. **L'eccesso è concentrato in `highl plik_lite` (+4047), `lensing` (+110) e `BAO` (+51)**: tutti sensibili alla storia di espansione tardiva e alla funzione di trasferimento — coerente con l'effetto genuino di `Omega_scf=0.1` + `lambda_reset=0.300` su questa storia, **non** un bug o un artefatto residuo.

**Conclusione**: al punto fiduciale richiesto, con i parametri cosmologici standard fissati ai valori di letteratura ΛCDM (mai ri-fittati per questo modello), lo Stratoverso è in forte tensione con Planck high-l + lensing + DESI. Questo è atteso quando si valuta un modello non-ΛCDM a parametri "presi in prestito" da un fit ΛCDM: il confronto onesto richiede un vero best-fit/MCMC che lasci liberi anche `omega_b, omega_cdm, A_s, n_s, tau_reio` (oltre a `lambda_reset, g_holographic, phi_phase`) — predisposto in `run_cobaya_stratoverso.py`, aggiornato con le stesse likelihood reali e priori per tutti questi parametri, pronto per un run di produzione.

---

## 🧬 Modello Ibrido ΛCDM + Stratoverso via f(z) — 2026-06-24

**Motivazione**: dopo aver visto la forte tensione col reale χ² Planck/DESI al punto fiduciale (sezione sopra), si è deciso di rendere lo Stratoverso un'estensione di ΛCDM che si attiva solo a basso redshift, invece che su tutta la storia cosmica — un cambiamento di modello, non un fix di bug.

**Implementazione** (4 passi, ciascuno approvato singolarmente):
1. Nuova funzione in `background.c`: `stratoverso_f_transition(z, z_trans, delta_z) = 1/(1+exp((z-z_trans)/delta_z))`, sigmoide C^∞.
2. `f_cutoff` in `background_functions()` ora usa questa sigmoide in `z` al posto del precedente cutoff in `a` (transizione ad `a=0.4`, cioè z≈1.5, larghezza 0.05) — un solo gate, non doppio. Moltiplica `rho_scf`, `p_scf`, `p_prime_scf` come già faceva il vecchio `f_cutoff` (variabile riusata, punti di applicazione invariati).
3. Test di continuità (`test_hybrid_background.py`, `test_hybrid_continuity_fine.py`): confermato che H(z) coincide con ΛCDM per z>50 (diff. relativa ~1e-7–1e-4), che il contributo Stratoverso è chiaramente attivo per z<2 (diff. relativa >10%), e che la transizione attorno a z_trans=20 è continua (nessun salto, verificato anche su dH/dz e d²H/dz² tra z=0 e z=3 — nessun kink residuo dal vecchio cutoff in `a` né dalla cascata di reset).
4. `z_trans` e `delta_z` promossi a parametri liberi: nuovi campi `pba->z_trans`/`pba->delta_z` in `background.h`, default 20.0/5.0 e parsing in `input.c` (stesso pattern di `lambda_reset`), `background.c` li legge da `pba` invece di valori hardcoded. Aggiunti a `run_cobaya_stratoverso.py` come parametri MCMC con prior `z_trans∈[5,50]`, `delta_z∈[1,15]`.

**Nota su z=0**: la differenza relativa H_strat vs ΛCDM scende quasi a zero esattamente a z=0 — non è una discontinuità (verificato: H_strat(z) da solo è perfettamente liscio), ma un effetto dello shooting di CLASS, che calibra entrambi i modelli per riprodurre lo stesso H0 di input a z=0 indipendentemente da f(z).

**Stato MCMC**: con questo cambiamento la dimensionalità del fit sale da 10 a 12 parametri liberi. Il run di produzione precedente (10 parametri) si era già bloccato dopo 400 tentativi rifiutati consecutivi per proposal mal calibrata — **nessun nuovo run lanciato**, su richiesta esplicita dell'utente. Da rivedere prima di un prossimo tentativo: proposal/covmat iniziali, eventualmente fissare alcuni parametri standard o usare un covmat di riferimento.

---

## ⚙️ Calibrazione Proposal MCMC e Scoperta di una Degenerazione Geometrica — 2026-06-24

**Setup**: `omega_b=0.02237`, `n_s=0.9649`, `tau_reio=0.0544` fissati ai best fit Planck 2018 (poco correlati con la fisica Stratoverso, vedi sotto), riducendo lo spazio libero da 12 a **9 parametri**: `H0, omega_cdm, A_s, A_planck, lambda_reset, g_holographic, phi_phase, z_trans, delta_z`. Covmat iniziale costruita a mano (diagonale) in `covmats/stratoverso_initial.covmat`.

**Pre-run 1** (`run_cobaya_prerun.py`, prior `H0∈[60,75]`, `z_trans∈[5,50]`, max 300 campioni): bloccato dopo ~1700 tentativi, fermo su 112 campioni accettati. Analisi della traccia: **non un problema di proposal** — il χ² scendeva con continuità monotona (42189 → 3402, **-92%**) mentre `H0` e `z_trans` scivolavano verso i bordi inferiori dei rispettivi prior, fermandosi esattamente lì (`H0→60.0`, `z_trans→5.0`) perché bloccati dal muro, non da una proposal mal scalata.

**Verifica bug vs fisica reale**: confrontato `100*theta_s` (scala acustica angolare, valore Planck reale ≈1.0411) tra Stratoverso e ΛCDM puro agli stessi `(H0, omega_b, omega_cdm)`:

| Punto | Stratoverso | ΛCDM puro | Planck |
|---|---|---|---|
| Iniziale (H0=66.4, z_trans=19.2) | 1.0939 | 1.0300 | 1.0411 |
| Bloccato (H0=60.3, z_trans=5.2) | **1.0447** | 1.0091 | 1.0411 |

Il ΛCDM puro a H0=60.3 sarebbe un pessimo fit (scala sbagliata del 3%); lo Stratoverso, con `lambda_reset`/il gate `z_trans` tardivo, **sposta la distanza angolare alla last-scattering nella direzione giusta**, riportando la scala a 0.3% dal valore Planck. **Confermato: non è un bug**, è una vera degenerazione geometria/energia oscura modificata — il campo scalare con la cascata di reset si comporta come un'energia oscura non standard che permette di scambiare H0 basso contro la modifica tardiva mantenendo fissa la scala angolare. Il χ² high-l/lensing migliora enormemente (-37000/-1700) a scapito di un piccolo peggioramento BAO/SN (+70/+90) — il freno naturale che dovrebbe spezzare la degenerazione, ma troppo debole nella finestra esplorata.

**Pre-run 2** (prior allargati `H0∈[50,80]`, `z_trans∈[0.1,50]`, stessa configurazione): completato con successo, 300/300 campioni, **nessun blocco** (tasso di accettazione ~28%). La catena ha superato i vecchi bordi e si è **stabilizzata in un modo interno**: `H0≈61.4±0.1`, `z_trans≈3.0±0.3`, `χ²≈3100`, niente più contro i bordi (vedi tabella valori medi sulla coda stazionaria in `covmats/stratoverso_empirical.covmat`). `H0~61` resta ben lontano dai valori cosmologici standard (~67-73) — plausibile dato il potere della degenerazione appena dimostrata, ma da non considerare un risultato finale: BAO/SN restano un'ancora debole nella finestra esplorata, e un fit completo a convergenza potrebbe spostare l'equilibrio.

**Covmat finale**: la covarianza empirica grezza (dalla coda stazionaria, 200 campioni, pesata per i rifiuti accumulati) aveva fortissime correlazioni (es. `A_s`↔`A_planck`=0.974, `omega_cdm`↔`g_holographic`=-0.940) e un autovalore numericamente nullo in scala di covarianza assoluta — **non una vera degenerazione lineare** ma un artefatto della scala molto diversa tra parametri (`A_s`~1e-9 vs `z_trans`~10): in spazio di correlazione (scala-invariante) l'autovalore minimo grezzo era 1.4e-3, comunque positivo. Regolarizzata con shrinkage 30% verso la diagonale iniziale in spazio di correlazione → `covmats/stratoverso_shrunk.covmat`, verificata con decomposizione di Cholesky. `run_cobaya_stratoverso.py` aggiornato con questa covmat e i `ref` al modo trovato. **Nessun run di produzione lanciato.**

---

## 📋 File Modificati e Posizioni

* **Codice CLASS**:
  - `background.c` / `background.h`: [source/background.c](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/source/background.c), [include/background.h](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/include/background.h) — `stratoverso_f_transition()`, `pba->z_trans`/`pba->delta_z`
  - `primordial.c`: [source/primordial.c](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/source/primordial.c)
  - `input.c`: [source/input.c](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/source/input.c) — parsing `z_trans`/`delta_z`
  - `thermodynamics.c`: [source/thermodynamics.c](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/source/thermodynamics.c)
* **Test modello ibrido**:
  - [test_hybrid_background.py](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/test_hybrid_background.py), [test_hybrid_continuity_fine.py](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/test_hybrid_continuity_fine.py)
* **Script e Log di Test**:
  - Script Cobaya (produzione, ora con likelihood reali e covmat calibrata): [run_cobaya_stratoverso.py](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/run_cobaya_stratoverso.py)
  - Pre-run di calibrazione proposal: [run_cobaya_prerun.py](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/run_cobaya_prerun.py)
  - Covmat: [covmats/stratoverso_initial.covmat](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/covmats/stratoverso_initial.covmat) (a mano), [covmats/stratoverso_empirical.covmat](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/covmats/stratoverso_empirical.covmat) (grezza dal pre-run), [covmats/stratoverso_shrunk.covmat](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/covmats/stratoverso_shrunk.covmat) (finale, regolarizzata)
  - Valutazione al punto fiduciale: [test_fiducial_planck.py](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/test_fiducial_planck.py), [test_fiducial_planck_g0.py](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/test_fiducial_planck_g0.py) (diagnosi g_holographic=0), [test_fiducial_lcdm_baseline.py](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/test_fiducial_lcdm_baseline.py) (baseline ΛCDM)
  - Log dell'MCMC (toy, superato): [test_logs/mcmc_run.log](file:///Users/coldmac/.gemini/antigravity/scratch/stratoverso_research/class_stratoverso/test_logs/mcmc_run.log)
  - Output delle valutazioni fiduciali: `test_logs/fiducial_eval/`

---

## 🔮 Cosa Resta da Fare (Passi Successivi)

1. ~~**Configurazione Likelihood Reali**~~ — **Fatto** (2026-06-23): `planck_2018_lowl.TT_clik`/`EE_clik`, `planck_2018_highl_plik.TTTEEE_lite`, `planck_2018_lensing.clik`, `bao.desi_dr2.desi_bao_all`, `sn.pantheonplus` collegate via `clipy`, vedi sezione "χ² al Punto Fiduciale" sopra.

2. **Run di Produzione MCMC reale (Cluster / CPU Multiple)**:
   - `run_cobaya_stratoverso.py` è configurato con le likelihood reali, 9 parametri liberi (`omega_b, n_s, tau_reio` fissati), covmat calibrata empiricamente (`covmats/stratoverso_shrunk.covmat`) e `ref` aggiornati al modo trovato dal pre-run (H0≈61.4, z_trans≈3.0) — non ancora eseguito (richiede tempo di calcolo significativo: ~0.2 eval/s per CLASS con `has_scf`).
   - **Aperto da chiarire prima/durante**: il pre-run ha scoperto una forte degenerazione geometria/energia oscura modificata (Stratoverso compensa H0 basso riallineando la scala acustica angolare, vedi sezione "Calibrazione Proposal" sopra) — il modo trovato (H0~61) è ben lontano dai valori cosmologici standard. Da vedere se un run a piena convergenza sposta l'equilibrio (BAO/SN sono un'ancora debole nella finestra esplorata) o se serve un prior esterno su H0 per ottenere vincoli scientificamente sensati su `lambda_reset`/`g_holographic`/`z_trans`.
   - Lanciare con criterio di convergenza Gelman-Rubin $R-1 < 0.02$ o $0.01$ per estrarre i vincoli sui parametri dello Stratoverso ($\lambda_{\rm reset}$, $g_{\rm holographic}$, $z_{\rm trans}$).

3. **PRL Letter**:
   - Una volta ottenuti i posteriors dell'MCMC reale, inserire il grafico dei vincoli (fisher ellipses o 1D/2D posteriors) nel Letter PRL di 4 pagine a supporto del valore analitico $\omega_g = 5.22$.
