# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/Latent-mixtureModels.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt

dset = 2

if dset==1:
    k = np.array([
        1,1,1,1,0,0,1,1,0,1,0,0,1,0,0,1,0,1,0,0,
        0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        0,0,1,0,0,0,1,1,0,0,0,0,1,0,0,0,0,0,0,0,
        0,0,0,0,0,0,1,0,1,1,0,0,0,0,0,0,0,0,0,0,
        1,0,1,1,0,1,1,1,0,1,0,0,1,0,0,0,0,1,0,0,
        1,1,0,1,0,0,0,1,0,1,0,1,1,0,0,1,0,1,0,0,
        0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        0,1,1,0,0,0,0,1,0,1,0,0,1,0,0,0,0,1,0,1,
        1,0,0,0,0,0,1,0,0,1,0,0,1,0,0,0,0,0,0,0
    ]).reshape(10,-1)
elif dset==2:
    k = np.ma.masked_values([
        1,1,1,1,0,0,1,1,0,1,0,0,-999,0,0,1,0,1,0,0,
        0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        0,0,1,0,0,0,1,1,0,0,0,0,1,0,0,0,0,0,0,0,
        0,0,0,0,0,0,1,0,1,1,0,0,0,0,0,0,0,0,0,0,
        1,0,1,1,0,1,1,1,0,1,0,0,1,0,0,0,0,1,0,0,
        1,1,0,1,0,0,0,1,0,1,0,1,1,0,0,1,0,1,0,0,
        0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,
        0,0,0,0,-999,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        0,1,1,0,0,0,0,1,0,1,0,0,1,0,0,0,0,1,0,1,
        1,0,0,0,0,0,1,0,0,1,0,0,1,0,0,0,0,-999,0,0
    ], value=-999).reshape(10,-1)

Np, Nq = k.shape

with pm.Model() as model3:
    # prior
    pi = pm.Beta("pi", alpha=1, beta=1, shape=Np)
    qi = pm.Beta("qi", alpha=1, beta=1, shape=Nq)
    # accuracy prior
    theta = pm.Deterministic("theta", tt.outer(pi, qi))
    # observed
    kij = pm.Bernoulli("kij", p=theta, observed=k)


model = model3

# MODELGRAPH:
# nodes:
# "pi", "qi", "theta", "kij"
# edges:
# "pi" -> "theta"
# "qi" -> "theta"
# "theta" -> "kij"
# END_MODELGRAPH

# NOTE pymc graph has kij_missing for missing data