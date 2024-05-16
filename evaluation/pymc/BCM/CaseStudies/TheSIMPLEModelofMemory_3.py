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

pc = pd.read_csv("data/pc_M.txt", sep=",", header=None) # added sep=
pcmat = np.asarray(pc).T

ymat = np.asarray(y)
nitem = m.shape[1]
m2 = m
m2[m2 == 0] = 1e-5  # to avoid NaN in ADVI
nmat = np.repeat(n[:, np.newaxis], nitem, axis=1)
mmat1 = np.repeat(m2[:, :, np.newaxis], nitem, axis=2)
mmat2 = np.transpose(mmat1, (0, 2, 1))
mask = np.where(ymat > 0)
W = listlength

with pm.Model() as simple2:
    cx = pm.Uniform("cx", lower=0, upper=100, testval=21)
    sx = pm.Uniform("sx", lower=0, upper=100, testval=10)
    a1 = pm.Uniform("a1", lower=-1, upper=0, testval=-0.002)
    a2 = pm.Uniform("a2", lower=0, upper=1, testval=0.64)
    tx = pm.Deterministic("tx", a1 * W + a2)

    # Similarities
    eta = tt.exp(-cx * abs(tt.log(mmat1) - tt.log(mmat2)))
    etasum = tt.reshape(tt.repeat(tt.sum(eta, axis=2), nitem), (dsets, nitem, nitem))

    # Discriminabilities
    disc = eta / etasum

    # Response Probabilities
    resp = 1 / (1 + tt.exp(-sx * (disc - tx[:, np.newaxis, np.newaxis])))

    # Free Recall Overall Response Probability
    # theta = tt.clip(tt.sum(resp, axis=2), 0., .999)
    theta = 1 - tt.prod(1 - resp, axis=2)

    yobs = pm.Binomial("yobs", p=theta[mask], n=nmat[mask], observed=ymat[mask])

model = simple2

# MODELGRAPH:
# nodes:
# "cx", "sx", "a1", "a2", "tx", "yobs"
# edges:
# "cx" -> "yobs"
# "sx" -> "yobs"
# "tx" -> "yobs"
# "a1" -> "tx"
# "a2" -> "tx"
# "tx" -> "yobs"
# END_MODELGRAPH


# NOTE: cannot infer constraint for input nmat