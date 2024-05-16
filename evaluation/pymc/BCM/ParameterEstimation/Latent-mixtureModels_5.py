# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/Latent-mixtureModels.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt

k = np.array([45,45,44,45,44,45,45,45,45,45,30,20,6,44,44,27,25,17,14,27,35,30])
p = len(k)  # number of people
n = 45  # number of questions

with pm.Model() as model5:
    # prior
    psib = pm.Uniform("psib", lower=0.5, upper=1.)
    psim = pm.Uniform("psim", lower=0., upper=psib)

    zi = pm.Bernoulli("zi", p=0.5, shape=p)

    theta = pm.Deterministic("theta", tt.switch(tt.eq(zi, 0), psib, psim))

    # observed
    kij = pm.Binomial("kij", p=theta, n=n, observed=k)

model = model5

# MODELGRAPH:
# nodes:
# "psib", "psim", "zi", "theta", "kij"
# edges:
# "psib" -> "theta"
# "psib" -> "psim"
# "psim" -> "theta"
# "zi" -> "theta"
# "theta" -> "kij"
# END_MODELGRAPH