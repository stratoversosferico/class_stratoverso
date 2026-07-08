from classy import Class

cosmo = Class()
cosmo.set({
    'H0': 67.4,
    'omega_b': 0.0224,
    'omega_cdm': 0.120,
    'Omega_scf': 0.1,
    'attractor_ic_scf': 'yes',
    'scf_parameters': '10.0, 0.0, 0.0, 0.0',
    'scf_tuning_index': 0,
    'lambda_reset': 0.300,
    'g_holographic': 0.014,
    'phi_phase': 3.14,
    'output': ''  # Background only
})
print("Calling compute() for background only...")
cosmo.compute()
print("Success!")
print("Age of the universe today (Gyr):", cosmo.age())
