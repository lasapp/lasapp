# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BDA3/chap_06.ipynb

import pymc3 as pm
import numpy as np

trials = np.array([1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0.])

with pm.Model() as model_2:
    
    theta = pm.Uniform('theta', lower=0, upper=1)
    obs = pm.Binomial('obs', n=trials.shape[0], p=theta, observed=np.sum(trials == 1))


model = model_2

# MODELGRAPH:
# nodes:
# 'theta', 'obs'
# edges:
# 'theta' -> 'obs'
# END_MODELGRAPH

