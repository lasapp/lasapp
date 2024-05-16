# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/CaseStudies/TheBARTModelofRiskTaking.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt
import pandas as pd

p = 0.15  # (Belief of) bursting probability
ntrials = 90  # Number of trials for the BART

Data = pd.read_csv("data/GeorgeSober.txt", sep="\t")
# Data.head()
cash = np.asarray(Data["cash"] != 0, dtype=int)
npumps = np.asarray(Data["pumps"], dtype=int)

options = cash + npumps

d = np.full([ntrials, 30], np.nan)
k = np.full([ntrials, 30], np.nan)
# response vector
for j, ipumps in enumerate(npumps):
    inds = np.arange(options[j], dtype=int)
    k[j, inds] = inds + 1
    if ipumps > 0:
        d[j, 0:ipumps] = 0
    if cash[j] == 1:
        d[j, ipumps] = 1

indexmask = np.isfinite(d)
d = d[indexmask]
k = k[indexmask]

with pm.Model() as model1: # as model1 added
    gammap = pm.Uniform("gammap", lower=0, upper=10, testval=1.2)
    beta = pm.Uniform("beta", lower=0, upper=10, testval=0.5)
    omega = pm.Deterministic("omega", -gammap / np.log(1 - p))

    thetajk = 1 - pm.math.invlogit(-beta * (k - omega))

    djk = pm.Bernoulli("djk", p=thetajk, observed=d)

model = model1

# MODELGRAPH:
# nodes:
# "gammap", "beta", "omega", "djk"
# edges:
# "gammap" -> "omega"
# "beta" -> "djk"
# "omega" -> "djk"
# END_MODELGRAPH