# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/Latent-mixtureModels.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt
import pandas as pd

# Load data
dat = pd.read_csv("data/cheat.csv", header=None)
truth = pd.read_csv("data/cheatt.csv", header=None)
k = np.array(dat.sum(axis=1))
t1 = truth.values.T

p = len(k)  # number of people
n = 40  # number of questions

with pm.Model() as model7:
    # prior
    mub = pm.Beta("mub", alpha=1, beta=1)
    mud = pm.HalfNormal("mud", sd=0.5)
    lambdab = pm.Uniform("lambdab", lower=5, upper=50)
    lambdac = pm.Uniform("lambdac", lower=5, upper=50)
    psi = pm.Beta("psi", alpha=5, beta=5)
    # psi = pm.Uniform("psi",lower=0,upper=1)
    zi = pm.Bernoulli("zi", p=psi, shape=p)

    muc = pm.Deterministic("muc", 1 / (1 + tt.exp(tt.log(1 / mub - 1) - mud)))
    theta1 = pm.Beta("theta1", alpha=mub * lambdab, beta=(1 - mub) * lambdab)
    theta2 = pm.Beta("theta2", alpha=muc * lambdac, beta=(1 - muc) * lambdac)

    theta = pm.Deterministic("theta", tt.switch(tt.eq(zi, 1), theta1, theta2))

    # observed
    kij = pm.Binomial("kij", p=theta, n=n, observed=k)

model = model7

# MODELGRAPH:
# nodes:
# "mub", "mud", "lambdab", "lambdac", "psi", "zi", "muc", "theta1", "theta2", "theta", "kij"
# edges:
# "mub" -> "muc"
# "mub" -> "theta1"
# "mud" -> "muc"
# "lambdab" -> "theta1"
# "lambdac" -> "theta2"
# "psi" -> "zi"
# "zi" -> "theta"
# "muc" -> "theta2"
# "theta1" -> "theta"
# "theta2" -> "theta"
# "theta" -> "kij"
# END_MODELGRAPH