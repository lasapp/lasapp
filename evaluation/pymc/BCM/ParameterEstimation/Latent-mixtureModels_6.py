# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/Latent-mixtureModels.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt

k = np.array([45,45,44,45,44,45,45,45,45,45,30,20,6,44,44,27,25,17,14,27,35,30])
p = len(k) # number of people
n = 45        # number of questions

with pm.Model() as model6:
    # prior
    mub = pm.Beta("mub", alpha=1, beta=1)
    mud = pm.HalfNormal("mud", sd=0.5)
    lambdab = pm.Uniform("lambdab", lower=40, upper=800)
    lambdam = pm.Uniform("lambdam", lower=4, upper=100)
    psi = pm.Beta("psi", alpha=5, beta=5)

    zi = pm.Bernoulli("zi", p=psi, shape=p)

    mum = pm.Deterministic("mum", 1 / (1 + tt.exp(tt.log(1 / mub - 1) + mud)))
    theta1 = pm.Beta("theta1", alpha=mub * lambdab, beta=(1 - mub) * lambdab)
    theta2 = pm.Beta("theta2", alpha=mum * lambdam, beta=(1 - mum) * lambdam)

    theta = pm.Deterministic("theta", tt.switch(tt.eq(zi, 0), theta1, theta2))

    # observed
    kij = pm.Binomial("kij", p=theta, n=n, observed=k)

model = model6

# MODELGRAPH:
# nodes:
# "mub", "mud", "lambdab", "lambdam", "psi", "zi", "mum", "theta1", "theta2", "theta", "kij"
# edges:
# "mub" -> "mum"
# "mub" -> "theta1"
# "mud" -> "mum"
# "lambdab" -> "theta1"
# "lambdam" -> "theta2"
# "psi" -> "zi"
# "zi" -> "theta"
# "mum" -> "theta2"
# "theta1" -> "theta"
# "theta2" -> "theta"
# "theta" -> "kij"
# END_MODELGRAPH