# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/CaseStudies/HeuristicDecisionMaking.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt
import scipy.io as sio

matdata = sio.loadmat("data/StopSearchData.mat")

y = np.squeeze(matdata["y"])
m = np.squeeze(np.float32(matdata["m"]))
p = np.squeeze(matdata["p"])
v = np.squeeze(np.float32(matdata["v"]))
x = np.squeeze(np.float32(matdata["x"]))

# Constants
n, nc = np.shape(m)  # number of stimuli and cues
nq, _ = np.shape(p)  # number of questions
ns, _ = np.shape(y)  # number of subjects

# Question cue contributions template
qcc = np.zeros((nq, nc))
for q in range(nq):
    # Add Cue Contributions To Mimic TTB Decision
    for j in range(nc):
        qcc[q, j] = m[p[q, 0] - 1, j] - m[p[q, 1] - 1, j]

qccmat = np.tile(qcc[np.newaxis, :, :], (ns, 1, 1))
# TTB Model For Each Question
s = np.argsort(v)  # s[1:nc] <- rank(v[1:nc])
smat = np.tile(s[np.newaxis, :], (ns, nq, 1))
ttmp = np.sum(qccmat * np.power(2, smat), axis=2)
tmat = -1 * (-ttmp > 0) + (ttmp > 0) + 1
t = tmat[0]
# tmat = np.tile(t[np.newaxis, :], (ns, 1))

# WADD Model For Each Question
xmat = np.tile(x[np.newaxis, :], (ns, nq, 1))
wtmp = np.sum(qccmat * xmat, axis=2)
wmat = -1 * (-wtmp > 0) + (wtmp > 0) + 1
w = wmat[0]

with pm.Model() as model4:
    phi = pm.Beta("phi", alpha=1, beta=1, testval=0.01)

    zi = pm.Bernoulli(
        "zi",
        p=phi,
        shape=ns,
        testval=np.asarray(
            [1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        ),
    )
    zi_ = tt.reshape(tt.repeat(zi, nq), (ns, nq))

    gamma = pm.Uniform("gamma", lower=0.5, upper=1)
    gammat = tt.stack([1 - gamma, 0.5, gamma])

    v1 = pm.HalfNormal("v1", sd=1, shape=ns * nc)
    s1 = pm.Deterministic("s1", tt.argsort(v1.reshape((ns, 1, nc)), axis=2))
    smat2 = tt.tile(s1, (1, nq, 1))  # s[1:nc] <- rank(v[1:nc])

    # TTB Model For Each Question
    ttmp = tt.sum(qccmat * tt.power(2, smat2), axis=2)
    tmat = -1 * (-ttmp > 0) + (ttmp > 0) + 1

    t2 = tt.switch(tt.eq(zi_, 1), tmat, wmat)
    yiq = pm.Bernoulli("yiq", p=gammat[t2], observed=y)

model = model4

# MODELGRAPH:
# nodes:
# "phi", "zi", "gamma", "v1", "s1", "yiq"
# edges:
# "phi" -> "zi"
# "zi" -> "yiq"
# "gamma" -> "yiq"
# "v1" -> "s1"
# "s1" -> "yiq"
# END_MODELGRAPH