# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/CaseStudies/TheGCMModelofCategorization.ipynb

import pymc as pm
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

with pm.Model() as model3:
    mu1w = pm.Uniform("mu1w", lower=0, upper=1, testval=0.05)
    delta = pm.Uniform("delta", lower=0, upper=1, testval=0.75)
    mu2w = pm.Deterministic("mu2w", tt.clip(mu1w + delta, 0, 1))

    sigmaw = pm.Uniform("sigmaw", lower=0.01, upper=1, testval=0.05)
    muc = pm.Uniform("muc", lower=0, upper=5, testval=1.4)
    sigmac = pm.Uniform("sigmac", lower=0.01, upper=3, testval=0.45)

    phic = pm.Uniform("phic", lower=0, upper=1, testval=0.1)
    phig = pm.Uniform("phig", lower=0, upper=1, testval=0.8)

    zck = pm.Bernoulli("zck", p=phic, shape=nsubj)
    zcg = pm.Bernoulli("zcg", p=phig, shape=nsubj)
    b = 0.5

    c = tt.clip(pm.Normal("c", mu=muc, sd=sigmac, shape=(1, 1, nsubj)), 0, 5)
    muw = pm.Deterministic("muw", tt.switch(tt.eq(zcg, 0), mu1w, mu2w))
    w = tt.clip(pm.Normal("w", mu=muw, sd=sigmaw, shape=(1, 1, nsubj)), 0, 1)

    sij = tt.exp(-c * (w * d1_t + (1 - w) * d2_t))

    sum_ajsij = tt.sum(a1 * sij, axis=1)
    sum_majsij = tt.sum((1 - a1) * sij, axis=1)

    ri1 = pm.Deterministic(
        "ri1", (b * sum_ajsij) / (b * sum_ajsij + (1 - b) * sum_majsij)
    )
    ri2 = tt.constant(np.ones((nstim, nsubj)) * 0.5)
    ri = pm.Deterministic("ri", tt.squeeze(tt.switch(tt.eq(zck, 0), ri1, ri2)))

    yi = pm.Binomial("yi", p=ri, n=nstim, observed=y2)

model = model3

# MODELGRAPH:
# nodes:
# "mu1w", "delta", "mu2w", "sigmaw", "muc", "sigmac", "phic", "phig", "zck", "zcg", "c", "muw", "w", "ri1", "ri", "yi"
# edges:
# "mu1w" -> "mu2w"
# "mu1w" -> "muw"
# "delta" -> "mu2w"
# "mu2w" -> "muw"
# "sigmaw" -> "w"
# "muc" -> "c"
# "sigmac" -> "c"
# "phic" -> "zck"
# "phig" -> "zcg"
# "zck" -> "ri"
# "zcg" -> "muw"
# "c" -> "ri1"
# "muw" -> "w"
# "w" -> "ri1"
# "ri1" -> "ri"
# "ri" -> "yi"
# END_MODELGRAPH

# NOTE: normalisation cannot be correctly computed with interval arithmetic