# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/CaseStudies/MultinomialProcessingTrees.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt
import theano

indiv_trial = []
Nt = 3
kall = np.array([[45, 24, 97, 254], [106, 41, 107, 166], [243, 64, 65, 48]])

kshared = theano.shared(kall[0, :])

with pm.Model() as model1:
    c = pm.Beta("c", alpha=1, beta=1)
    r = pm.Beta("r", alpha=1, beta=1)
    u = pm.Beta("u", alpha=1, beta=1)

    t1 = c * r
    t2 = (1 - c) * (u ** 2)
    t3 = 2 * u * (1 - c) * (1 - u)
    t4 = c * (1 - r) + (1 - c) * (1 - u) ** 2

    kobs = pm.Multinomial("kobs", p=[t1, t2, t3, t4], n=kshared.sum(), observed=kshared)

model = model1

# MODELGRAPH:
# nodes:
# "c", "r", "u", "kobs"
# edges:
# "c" -> "kobs"
# "r" -> "kobs"
# "u" -> "kobs"
# END_MODELGRAPH

# NOTE: cannot verify simplex constraint