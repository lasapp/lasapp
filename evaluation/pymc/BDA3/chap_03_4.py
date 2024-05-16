# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BDA3/chap_03.ipynb

import pymc3 as pm
import numpy as np

x_dose = np.array([-0.86, -0.3, -0.05, 0.73])
n_anim = np.array([5, 5, 5, 5])
y_deat = np.array([0, 1, 3, 5])

with pm.Model() as model_5:
    alpha = pm.Uniform('alpha', lower=-5, upper=7)
    beta = pm.Uniform('beta', lower=0, upper=50)
    
    theta = pm.math.invlogit(alpha + beta * x_dose)
    
    post = pm.Binomial('post', n=n_anim, p=theta, observed=y_deat)


model = model_5

# MODELGRAPH:
# nodes:
# 'alpha', 'beta', 'post'
# edges:
# 'alpha' -> 'post'
# 'beta' -> 'post'
# END_MODELGRAPH