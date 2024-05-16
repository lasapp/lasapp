# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/CaseStudies/NumberConceptDevelopment.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt
import scipy.io as sio

matdata = sio.loadmat("data/fc_given.mat")

ns = np.squeeze(np.int64(matdata["ns"]))
nz = np.squeeze(np.int64(matdata["nz"]))
gnq = np.squeeze(np.int64(matdata["gnq"]))
gn = np.squeeze(np.int64(matdata["gn"]))
ga = np.squeeze(np.int64(matdata["ga"]))
gq = np.squeeze(np.int64(matdata["gq"]))

ind5 = np.zeros((nz, gn, gn), dtype=int)
for i in range(nz):
    i1 = i + 1
    for j in range(gn):
        j1 = j + 1
        for k in range(gn):
            k1 = k + 1
            # Will be 1 if Knower-Level is Same or Greater than Answer
            ind1 = int(i1 - 1 >= k1)
            # Will be 1 for the Possible Answer that Matches the Question
            ind2 = int(k1 == j1)
            # Will be 1 for 0-Knowers
            ind3 = int(i1 == 1)
            # Will be 1 for HN-Knowers
            ind4 = int(i1 == nz)
            ind5[i, j, k] = (
                ind3
                + ind4 * (2 + ind2)
                + (1 - ind4) * (1 - ind3) * (ind1 * ind2 + ind1 + 1)
            )

ind5r = ind5 - 1
ga_obs = np.asarray(ga.flatten() - 1, dtype=int)
gq_obs = np.asarray(gq.flatten() - 1, dtype=int)
valid_ind = np.where(gq_obs != -1)[0]

with pm.Model() as model1:
    pi = pm.Dirichlet("pi", a=np.ones(gn), shape=gn)

    nu = pm.Uniform("nu", lower=1, upper=1000)
    nu_vec = tt.stack([1.0, 1.0 / nu, nu])

    piprime = tt.mul(nu_vec[ind5r], pi)
    npiprime = piprime / tt.sum(piprime, axis=-1, keepdims=True)

    zi = pm.Categorical("zi", p=np.ones(nz) / nz, shape=ns)
    zi_vec = tt.repeat(zi, gq.shape[1])

    pi_ij = npiprime[zi_vec[valid_ind], gq_obs[valid_ind], :]

    aij = pm.Categorical("aij", p=pi_ij, observed=ga_obs[valid_ind])


model = model1

# MODELGRAPH:
# nodes:
# "pi", "nu", "zi", "aij"
# edges:
# "pi" -> "aij"
# "nu" -> "aij"
# "zi" -> "aij"
# END_MODELGRAPH

# NOTE: cannot verify simplex constraint