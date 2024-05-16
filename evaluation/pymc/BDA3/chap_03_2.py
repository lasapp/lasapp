# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BDA3/chap_03.ipynb

import pymc3 as pm
import numpy as np

obs = np.array([727, 583, 137])

with pm.Model() as model_3:

    theta1 = pm.Uniform('theta1', lower=0, upper=1)
    theta2 = pm.Uniform('theta2', lower=0, upper=1)
    theta3 = pm.Uniform('theta3', lower=0, upper=1)
    post = pm.Multinomial('post', n=obs.sum(), p=[theta1, theta2, theta3], observed=obs)
    
    diff = pm.Deterministic('diff', theta1 - theta2)


model = model_3

# MODELGRAPH:
# nodes:
# 'theta1', 'theta2', 'theta3', 'post', 'diff'
# edges:
# 'theta1' -> 'post'
# 'theta2' -> 'post'
# 'theta3' -> 'post'
# 'theta1' -> 'diff'
# 'theta2' -> 'diff'
# END_MODELGRAPH

# NOTE: simplex constraint cannot be verified with intervals