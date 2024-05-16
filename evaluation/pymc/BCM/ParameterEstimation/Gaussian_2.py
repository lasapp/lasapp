# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/Gaussian.ipynb

import pymc3 as pm
import numpy as np

# data
x = np.array([-27.020, 3.570, 8.191, 9.898, 9.603, 9.945, 10.056])
n = len(x)

with pm.Model() as model2:
    # prior
    mu = pm.Normal("mu", mu=0., tau=0.001)
    lambda1 = pm.Gamma("lambda1", alpha=0.01, beta=0.01, shape=n)
    # sigma = pm.Deterministic('sigma',1 / sqrt(lambda1))
    # observed
    xi = pm.Normal("xi", mu=mu, tau=lambda1, observed=x)

model = model2

# MODELGRAPH:
# nodes:
# "mu", "lambda1", "xi"
# edges:
# "mu" -> "xi"
# "lambda1" -> "xi"
# END_MODELGRAPH