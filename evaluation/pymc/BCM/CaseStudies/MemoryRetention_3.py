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

t2 = np.array([1, 2, 4, 7, 12, 21, 35, 59, 99])
nt2 = len(t2)
# slist = [0,1,2,3]
ns2 = 3
tmat2 = np.repeat(t2, ns2).reshape(nt2, -1).T
k2 = np.asarray([18, 18, 16, 13, 9, 6, 4, 4, 4, 
                 17, 13,  9,  6, 4, 4, 4, 4, 4, 
                 14, 10,  6,  4, 4, 4, 4, 4, 4]).reshape(ns2,-1)

with pm.Model() as model2_:
    alpha = pm.Beta(
        "alpha",
        alpha=1,
        beta=1,
        shape=(1, ns),
        testval=np.asarray([[0.3, 0.3, 0.3, 0.5]]),
    )
    beta = pm.Beta(
        "beta",
        alpha=1,
        beta=1,
        shape=(1, ns),
        testval=np.asarray([[0.25, 0.25, 0.25, 0.5]]),
    )

    theta = (tt.exp(-alpha[:, :ns2] * t2[:, None]) + beta[:, :ns2]).T
    thetaj = pm.Deterministic("thetaj", tt.clip(theta, 0, 1))

    kij = pm.Binomial("kij", p=thetaj, n=n, observed=k2)

    # generate ppc
    theta2 = tt.minimum((tt.exp(-alpha * t[:, None]) + beta).T, 1.0)
    # rng = tt.shared_randomstreams.RandomStreams()
    # kij_ppc = pm.Deterministic("kij_ppc", rng.binomial(n=n, p=theta2))
    rng = tt.random.utils.RandomStream()
    kij_ppc = pm.Deterministic("kij_ppc", rng.binomial(n, theta2))

model = model2_

# MODELGRAPH:
# nodes:
# "alpha", "beta", "thetaj", "kij", "kij_ppc"
# edges:
# "alpha" -> "thetaj"
# "beta" -> "thetaj"
# "thetaj" -> "kij"
# "alpha" -> "kij_ppc"
# "beta" -> "kij_ppc"
# END_MODELGRAPH