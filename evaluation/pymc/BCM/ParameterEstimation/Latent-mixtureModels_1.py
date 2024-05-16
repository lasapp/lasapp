# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/Latent-mixtureModels.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt

k = np.array([21, 17, 21, 18, 22, 31, 31, 34, 34, 35, 35, 36, 39, 36, 35])
p = len(k)  # number of people
n = 40  # number of questions

with pm.Model() as model1:
    # group prior
    zi = pm.Bernoulli("zi", p=0.5, shape=p)
    # accuracy prior
    phi = pm.Uniform("phi", upper=1, lower=0.5)
    psi = 0.5
    theta = pm.Deterministic("theta", phi * tt.eq(zi, 1) + psi * tt.eq(zi, 0))

    # observed
    ki = pm.Binomial("ki", p=theta, n=n, observed=k)


model = model1

# MODELGRAPH:
# nodes:
# "zi", "phi", "theta", "ki"
# edges:
# "zi" -> "theta"
# "phi" -> "theta"
# "theta" -> "ki"
# END_MODELGRAPH

# NOTE: over approximates  tt.eq(zi, 1) + tt.eq(zi, 0) as [0,2]