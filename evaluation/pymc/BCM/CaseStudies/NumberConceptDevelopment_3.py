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

ind5r = ind5 - 1
ga_obs = np.asarray(ga.flatten() - 1, dtype=int)
gq_obs = np.asarray(gq.flatten() - 1, dtype=int)
valid_ind1 = np.where(gq_obs != -1)[0]

find5r = find5 - 1
fa_obs = np.asarray(fa.flatten() - 1, dtype=int)
fq_obs = np.asarray(fq.flatten() - 1, dtype=int)
valid_ind2 = np.where(fq_obs != -1)[0]

with pm.Model() as model3:
    # Knower level (same for each subject)
    zi = pm.Categorical("zi", p=np.ones(nz) / nz, shape=ns)

    # Give-N
    pi_g = pm.Dirichlet("pi_g", a=np.ones(gn), shape=gn)
    nug = pm.Uniform("nu_g", lower=1, upper=1000)
    nug_vec = tt.stack([1.0, 1.0 / nug, nug])

    piprimeg = tt.mul(nug_vec[ind5r], pi_g)
    npiprimeg = piprimeg / tt.sum(piprimeg, axis=-1, keepdims=True)
    zig_vec = tt.repeat(zi, gq.shape[1])
    pig_ij = npiprimeg[zig_vec[valid_ind1], gq_obs[valid_ind1], :]

    agij = pm.Categorical("ag_ij", p=pig_ij, observed=ga_obs[valid_ind1])

    # Fast-Cards
    pi_f = pm.Dirichlet("pi_f", a=np.ones(fn), shape=fn)
    nuf = pm.Uniform("nu_f", lower=1, upper=1000)
    nuf_vec = tt.stack([1.0, 1.0 / nuf, nuf])

    piprimef = tt.mul(nuf_vec[find5r], pi_f)
    npiprimef = piprimef / tt.sum(piprimef, axis=-1, keepdims=True)
    zif_vec = tt.repeat(zi, fq.shape[1])

    pif_ij = npiprimef[zif_vec[valid_ind2], fq_obs[valid_ind2], :]

    afij = pm.Categorical("af_ij", p=pif_ij, observed=fa_obs[valid_ind2])

model = model3

# MODELGRAPH:
# nodes:
# "pi_g", "nu_g", "zi", "ag_ij", "pi_f", "nu_f", "af_ij"
# edges:
# "zi" -> "ag_ij"
# "zi" -> "af_ij"
# "pi_g" -> "ag_ij"
# "nu_g" -> "ag_ij"
# "pi_f" -> "af_ij"
# "nu_f" -> "af_ij"
# END_MODELGRAPH


# NOTE: cannot verify simplex constraint