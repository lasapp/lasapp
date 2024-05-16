# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/CaseStudies/TheSIMPLEModelofMemory.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt
import pandas as pd

y = pd.read_csv("data/k_M.txt", sep=",", header=None) # added sep=
n = np.array([1440, 1280, 1520, 1520, 1200, 1280])
listlength = np.array([10, 15, 20, 20, 30, 40])
lagall = np.array([2, 2, 2, 1, 1, 1])
offset = np.array([15, 20, 25, 10, 15, 20])
dsets = 6
m = np.zeros(np.shape(y))

for i in range(dsets):
    m[i, 0 : listlength[i]] = offset[i] + np.arange(
        (listlength[i]) * lagall[i], 0, -lagall[i]
    )
    
ymat = np.asarray(y).T
mmat = m.T
W = listlength

with pm.Model() as simple2:
    cx = pm.Uniform("cx", lower=0, upper=100, testval=21)
    sx = pm.Uniform("sx", lower=0, upper=100, testval=10)
    a1 = pm.Uniform("a1", lower=-1, upper=0, testval=-0.002)
    a2 = pm.Uniform("a2", lower=0, upper=1, testval=0.64)
    tx = pm.Deterministic("tx", a1 * W + a2)

    yobs = []
    for x in range(dsets):
        sz = listlength[x]
        # Similarities
        m1 = np.array([mmat[0:sz, x],] * sz).T
        m2 = np.array([mmat[0:sz, x],] * sz)

        eta = tt.exp(-cx * abs(tt.log(m1) - tt.log(m2)))
        etasum = tt.reshape(tt.repeat(tt.sum(eta, axis=1), sz), (sz, sz))
        # Discriminabilities
        disc = eta / etasum
        # Response Probabilities
        resp = 1 / (1 + tt.exp(-sx * (disc - tx[x])))
        # Free Recall Overall Response Probability
        theta = tt.clip(tt.sum(resp, axis=1), 0, 0.999)
        # theta=1-tt.prod(1-resp,axis=1)

        yobs.append(
            [pm.Binomial("yobs_%x" % x, p=theta, n=n[x], observed=ymat[0:sz, x])]
        )

model = simple2

# MODELGRAPH:
# nodes:
# "cx", "sx", "a1", "a2", "tx", "yobs_%x" % x
# edges:
# "cx" -> "yobs_%x" % x
# "sx" -> "yobs_%x" % x
# "tx" -> "yobs_%x" % x
# "a1" -> "tx"
# "a2" -> "tx"
# "tx" -> "yobs_%x" % x
# END_MODELGRAPH

# NOTE: for loop
# NOTE: pymc graph is different due to loop