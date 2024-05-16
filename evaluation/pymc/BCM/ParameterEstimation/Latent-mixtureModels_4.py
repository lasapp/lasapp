# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/Latent-mixtureModels.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt

dset = 3

if dset==1:
    k = np.array([
        1,0,0,1,1,0,0,1,
      1,0,0,1,1,0,0,1,
      0,1,1,0,0,1,0,0,
      0,1,1,0,0,1,1,0,
      1,0,0,1,1,0,0,1,
      0,0,0,1,1,0,0,1,
      0,1,0,0,0,1,1,0,
      0,1,1,1,0,1,1,0
    ]).reshape(8,-1)
elif dset==2:
    k = np.ma.masked_values([
        1,0,0,1,1,0,0,1,
      1,0,0,1,1,0,0,1,
      0,1,1,0,0,1,0,0,
      0,1,1,0,0,1,1,0,
      1,0,0,1,1,0,0,1,
      0,0,0,1,1,0,0,1,
      0,1,0,0,0,1,1,0,
      0,1,1,1,0,1,1,0,
      1,0,0,1,-999,-999,-999,-999,
      0,-999,-999,-999,-999,-999,-999,-999,
      -999,-999,-999,-999,-999,-999,-999,-999
    ], value=-999).reshape(11,-1)
elif dset==3:
    k = np.ma.masked_values([
        1,0,0,1,1,0,0,1,
      1,0,0,1,1,0,0,1,
      1,0,0,1,1,0,0,1,
      1,0,0,1,1,0,0,1,
      1,0,0,1,1,0,0,1,
      1,0,0,1,1,0,0,1,
      1,0,0,1,1,0,0,1,
      1,0,0,1,1,0,0,1,
      1,0,0,1,1,0,0,1,
      1,0,0,1,1,0,0,1,
      1,0,0,1,1,0,0,1,
      1,0,0,1,1,0,0,1,
      0,1,1,0,0,1,0,0,
      0,1,1,0,0,1,1,0,
      1,0,0,1,1,0,0,1,
      0,0,0,1,1,0,0,1,
      0,1,0,0,0,1,1,0,
      0,1,1,1,0,1,1,0,
      1,0,0,1,-999,-999,-999,-999,
      0,-999,-999,-999,-999,-999,-999,-999,
      -999,-999,-999,-999,-999,-999,-999,-999
    ], value=-999).reshape(21,-1)

Nx, Nz = k.shape

with pm.Model() as model4:
    # prior
    alpha = pm.Uniform("alpha", lower=0., upper=1.)
    beta = pm.Uniform("beta", lower=0., upper=alpha)

    xi = pm.Bernoulli("xi", p=0.5, shape=(Nx, 1))
    zj = pm.Bernoulli("zj", p=0.5, shape=(1, Nz))

    # accuracy prior
    theta = pm.Deterministic("theta", tt.switch(tt.eq(xi, zj), alpha, beta))

    # observed
    kij = pm.Bernoulli("kij", p=theta, observed=k)


model = model4

# MODELGRAPH:
# nodes:
# "alpha", "beta", "xi", "zj", "theta", "kij"
# edges:
# "alpha" -> "theta"
# "alpha" -> "beta"
# "beta" -> "theta"
# "xi" -> "theta"
# "zj" -> "theta"
# "theta" -> "kij"
# END_MODELGRAPH


# NOTE pymc graph has kij_missing for missing data