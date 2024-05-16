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

fnq = np.squeeze(np.int64(matdata["fnq"]))
fa = np.squeeze(np.int64(matdata["fa"]))
fq = np.squeeze(np.int64(matdata["fq"]))
fn = 50

find5 = np.zeros((nz, gn, fn), dtype=int)
for i in range(nz):
    i1 = i + 1
    for j in range(gn):
        j1 = j + 1
        for k in range(fn):
            k1 = k + 1
            # Will be 1 if Knower-Level is Same or Greater than Answer
            find1 = int(i1 - 1 >= k1)
            # Will be 1 for the Possible Answer that Matches the Question
            find2 = int(k1 == j1)
            # Will be 1 for 0-Knowers
            find3 = int(i1 == 1)
            # Will be 1 for HN-Knowers
            find4 = int(i1 == nz)
            find5[i, j, k] = (
                find3
                + find4 * (2 + find2)
                + (1 - find4) * (1 - find3) * (find1 * find2 + find1 + 1)
            )

find5r = find5 - 1
fa_obs = np.asarray(fa.flatten() - 1, dtype=int)
fq_obs = np.asarray(fq.flatten() - 1, dtype=int)
valid_ind2 = np.where(fq_obs != -1)[0]


with pm.Model() as model2:
    pi = pm.Dirichlet("pi", a=np.ones(fn), shape=fn)

    nu = pm.Uniform("nu", lower=1, upper=1000)
    nu_vec = tt.stack([1.0, 1.0 / nu, nu])

    piprime = tt.mul(nu_vec[find5r], pi)
    npiprime = piprime / tt.sum(piprime, axis=-1, keepdims=True)

    zi = pm.Categorical("zi", p=np.ones(nz) / nz, shape=ns)
    zi_vec = tt.repeat(zi, fq.shape[1])

    pi_ij = npiprime[zi_vec[valid_ind2], fq_obs[valid_ind2], :]

    aij = pm.Categorical("aij", p=pi_ij, observed=fa_obs[valid_ind2])


model = model2

# MODELGRAPH:
# nodes:
# "pi", "nu", "zi", "aij"
# edges:
# "pi" -> "aij"
# "nu" -> "aij"
# "zi" -> "aij"
# END_MODELGRAPH

# NOTE: cannot verify simplex constraint