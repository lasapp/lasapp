# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/Latent-mixtureModels.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt

# pymc - need some tuning to get the same result as in JAGS
k = np.array([21, 17, 21, 18, 22, 31, 31, 34, 34, 35, 35, 36, 39, 36, 35])
p = len(k)  # number of people
n = 40  # number of questions

with pm.Model() as model2:
    # group prior
    zi = pm.Bernoulli("zi", p=0.5, shape=p)
    # accuracy prior
    psi = 0.5
    mu = pm.Uniform("mu", upper=1, lower=0.5)
    lambda_ = pm.Gamma("lambda_", alpha=0.001, beta=0.001)
    phi = pm.Bound(pm.Normal, 0, 1)("phi", mu=mu, tau=lambda_, shape=p)

    theta = pm.Deterministic("theta", tt.switch(tt.eq(zi, 1), phi, psi))

    # observed
    ki = pm.Binomial("ki", p=theta, n=n, observed=k)

model = model2

# MODELGRAPH:
# nodes:
# "zi", "mu", "lambda_", "phi", "theta", "ki"
# edges:
# "zi" -> "theta"
# "mu" -> "phi"
# "lambda_" -> "phi"
# "phi" -> "theta"
# "theta" -> "ki"
# END_MODELGRAPH