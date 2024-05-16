# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/DataAnalysis.ipynb

import pymc3 as pm
import numpy as np

# CHOOSE a data set:
# Influenza
y = np.array([14, 4, 5, 210])
# Hearing Loss
# y = np.array([20, 7, 103, 417])
# Rare Disease
# y = np.array([0, 0, 13, 157])

with pm.Model() as model3:
    # prior
    alpha = pm.Beta("alpha", alpha=1, beta=1)
    beta = pm.Beta("beta", alpha=1, beta=1)
    gamma = pm.Beta("gamma", alpha=1, beta=1)

    pi1 = alpha * beta
    pi2 = alpha * (1 - beta)
    pi3 = (1 - alpha) * (1 - gamma)
    pi4 = (1 - alpha) * gamma

    # Derived Measures
    # Rate Surrogate Method Agrees With the Objective Method
    xi = alpha * beta + (1 - alpha) * gamma

    yd = pm.Multinomial("yd", n=y.sum(), p=[pi1, pi2, pi3, pi4], observed=y)

    # Rate of Chance Agreement
    psi = pm.Deterministic("psi", (pi1 + pi2) * (pi1 + pi3) + (pi2 + pi4) * (pi3 + pi4))

    # Chance-Corrected Agreement
    kappa = pm.Deterministic("kappa", (xi - psi) / (1 - psi))

model = model3

# MODELGRAPH:
# nodes:
# "alpha", "beta", "gamma", "yd", "psi", "kappa"
# edges:
# "alpha" -> "kappa"
# "beta" -> "kappa"
# "gamma" -> "kappa"
# "alpha" -> "psi"
# "beta" -> "psi"
# "gamma" -> "psi"
# "alpha" -> "yd"
# "beta" -> "yd"
# "gamma" -> "yd"
# "psi" -> "kappa"
# END_MODELGRAPH

# NOTE: cannot verify simplex constraint