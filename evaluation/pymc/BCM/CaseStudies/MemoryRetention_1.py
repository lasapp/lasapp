# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/CaseStudies/MemoryRetention.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt

t = np.array([1, 2, 4, 7, 12, 21, 35, 59, 99, 200])
nt = len(t)
# slist = [0,1,2,3]
ns = 4
tmat = np.repeat(t, ns).reshape(nt, -1).T
k1 = np.ma.masked_values([18, 18, 16, 13, 9, 6, 4, 4, 4, -999,
                          17, 13,  9,  6, 4, 4, 4, 4, 4, -999,
                          14, 10,  6,  4, 4, 4, 4, 4, 4, -999,
                          -999, -999, -999, -999, -999, -999, -999, -999, -999, -999], 
                          value=-999).reshape(ns,-1) # fixed 1 -> k1
n = 18

with pm.Model() as model1:
    # prior
    alpha = pm.Beta("alpha", alpha=1, beta=1, testval=0.30)
    beta = pm.Beta("beta", alpha=1, beta=1, testval=0.25)

    # parameter transformation
    theta = tt.exp(-alpha * tmat) + beta
    # thetaj = pm.Deterministic('thetaj', tt.clip(theta, 0, 1))
    thetaj = pm.Deterministic("thetaj", tt.minimum(theta, 1))

    kij = pm.Binomial("kij", p=thetaj, n=n, observed=k1)

model = model1

# MODELGRAPH:
# nodes:
# "alpha", "beta", "thetaj", "kij"
# edges:
# "alpha" -> "thetaj"
# "beta" -> "thetaj"
# "thetaj" -> "kij"
# END_MODELGRAPH

# NOTE pymc graph has kij_missing for missing data