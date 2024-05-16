# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/CaseStudies/TheBARTModelofRiskTaking.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt
import pandas as pd

p = 0.15  # (Belief of) bursting probability
ntrials = 90  # Number of trials for the BART
Ncond = 3

dall = np.full([Ncond, ntrials, 30], np.nan)
options = np.zeros((Ncond, ntrials))
kall = np.full([Ncond, ntrials, 30], np.nan)
npumps_ = np.zeros((Ncond, ntrials))

for icondi in range(Ncond):
    if icondi == 0:
        Data = pd.read_csv("data/GeorgeSober.txt", sep="\t")
    elif icondi == 1:
        Data = pd.read_csv("data/GeorgeTipsy.txt", sep="\t")
    elif icondi == 2:
        Data = pd.read_csv("data/GeorgeDrunk.txt", sep="\t")
    # Data.head()
    cash = np.asarray(Data["cash"] != 0, dtype=int)
    npumps = np.asarray(Data["pumps"], dtype=int)
    npumps_[icondi, :] = npumps
    options[icondi, :] = cash + npumps
    # response vector
    for j, ipumps in enumerate(npumps):
        inds = np.arange(options[icondi, j], dtype=int)
        kall[icondi, j, inds] = inds + 1
        if ipumps > 0:
            dall[icondi, j, 0:ipumps] = 0
        if cash[j] == 1:
            dall[icondi, j, ipumps] = 1

indexmask = np.isfinite(dall)
dij = dall[indexmask]
kij = kall[indexmask]
condall = np.tile(np.arange(Ncond, dtype=int), (30, ntrials, 1))
condall = np.swapaxes(condall, 0, 2)
cij = condall[indexmask]

chains = 2
with pm.Model() as model2:
    mu_g = pm.Uniform("mu_g", lower=0, upper=10)
    sigma_g = pm.Uniform("sigma_g", lower=0, upper=10)
    mu_b = pm.Uniform("mu_b", lower=0, upper=10)
    sigma_b = pm.Uniform("sigma_b", lower=0, upper=10)

    gammap = pm.Normal("gammap", mu=mu_g, sd=sigma_g, shape=Ncond)
    beta = pm.Normal("beta", mu=mu_b, sd=sigma_b, shape=Ncond)

    omega = -gammap[cij] / np.log(1 - p)
    thetajk = 1 - pm.math.invlogit(-beta[cij] * (kij - omega))

    djk = pm.Bernoulli("djk", p=thetajk, observed=dij)

model = model2

# MODELGRAPH:
# nodes:
# "mu_g", "sigma_g", "mu_b", "sigma_b", "gammap", "beta", "djk"
# edges:
# "mu_g" -> "gammap"
# "sigma_g" -> "gammap"
# "mu_b" -> "beta"
# "sigma_b" -> "beta"
# "gammap" -> "djk"
# "beta" -> "djk"
# END_MODELGRAPH