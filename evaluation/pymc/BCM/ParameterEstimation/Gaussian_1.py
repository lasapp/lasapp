# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/Gaussian.ipynb

import pymc3 as pm
import numpy as np

# Data
x = np.array([1.1, 1.9, 2.3, 1.8])
n = len(x)

with pm.Model() as model1:
    # prior
    mu = pm.Normal("mu", mu=0., tau=0.001)
    sigma = pm.Uniform("sigma", lower=0., upper=10.)
    # observed
    xi = pm.Normal("xi", mu=mu, tau=1 / (sigma ** 2), observed=x)

model = model1

# MODELGRAPH:
# nodes:
# "mu", "sigma", "xi"
# edges:
# "mu" -> "xi"
# "sigma" -> "xi"
# END_MODELGRAPH