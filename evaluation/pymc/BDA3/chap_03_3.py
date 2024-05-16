# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BDA3/chap_03.ipynb

import pymc3 as pm
import numpy as np

obs = np.array([727, 583, 137])

with pm.Model() as model_4:
    theta = pm.Dirichlet('theta', a=np.ones_like(obs))
    post = pm.Multinomial('post', n=obs.sum(), p=theta, observed=obs)


model = model_4

# MODELGRAPH:
# nodes:
# 'theta', 'post'
# edges:
# 'theta' -> 'post'
# END_MODELGRAPH

# NOTE: simplex constraint cannot be verified with intervals