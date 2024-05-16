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

s = np.argsort(v)  # s[1:nc] <- rank(v[1:nc])
t = []
# TTB Model For Each Question
for q in range(nq):
    # Add Cue Contributions To Mimic TTB Decision
    tmp1 = np.zeros(nc)
    for j in range(nc):
        tmp1[j] = (m[p[q, 0] - 1, j] - m[p[q, 1] - 1, j]) * np.power(2, s[j])
    # Find if Cue Favors First, Second, or Neither Stimulus
    tmp2 = np.sum(tmp1)
    tmp3 = -1 * np.float32(-tmp2 > 0) + np.float32(tmp2 > 0)
    t.append(tmp3 + 1)

t = np.asarray(t, dtype=int)
tmat = np.tile(t[np.newaxis, :], (ns, 1))

with pm.Model() as model1:
    gamma = pm.Uniform("gamma", lower=0.5, upper=1)
    gammat = tt.stack([1 - gamma, 0.5, gamma])

    yiq = pm.Bernoulli("yiq", p=gammat[tmat], observed=y)

model = model1

# MODELGRAPH:
# nodes:
# "gamma", "yiq"
# edges:
# "gamma" -> "yiq"
# END_MODELGRAPH