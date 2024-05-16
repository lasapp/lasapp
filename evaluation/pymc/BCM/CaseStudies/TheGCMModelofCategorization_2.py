# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/CaseStudies/TheGCMModelofCategorization.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt
import scipy.io as sio

matdata = sio.loadmat("data/KruschkeData.mat")

nstim = 8
nsubj = 40
t = nstim * nsubj
a = matdata["a"][0]
y = matdata["y"][:, 0]

d1 = matdata["d1"]
d2 = matdata["d2"]
x = matdata["x"]

x2 = np.float32(x)

a1 = np.tile(2 - a, [nstim, 1])[:, :, np.newaxis]
y2 = x2.transpose()
d1_t = np.tile(d1[:, :, np.newaxis], [1, 1, nsubj])
d2_t = np.tile(d2[:, :, np.newaxis], [1, 1, nsubj])

with pm.Model() as model2:
    c = pm.Uniform("c", lower=0, upper=5, shape=(1, 1, nsubj))
    w = pm.Uniform("w", lower=0, upper=1, shape=(1, 1, nsubj))
    b = 0.5

    sij = tt.exp(-c * (w * d1_t + (1 - w) * d2_t))

    sum_ajsij = tt.sum(a1 * sij, axis=1)
    sum_majsij = tt.sum((1 - a1) * sij, axis=1)

    ri = pm.Deterministic(
        "ri", (b * sum_ajsij) / (b * sum_ajsij + (1 - b) * sum_majsij)
    )

    yi = pm.Binomial("yi", p=ri, n=nstim, observed=y2)

model = model2

# MODELGRAPH:
# nodes:
# "c", "w", "ri", "yi"
# edges:
# "c" -> "ri"
# "w" -> "ri"
# "ri" -> "yi"
# END_MODELGRAPH


# NOTE: normalisation cannot be correctly computed with interval arithmetic