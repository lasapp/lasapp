# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BDA3/chap_05.ipynb

import pymc3 as pm
import numpy as np

rat_tumor = np.loadtxt('data/rat_tumor_data.txt', skiprows=3)

with pm.Model() as model_1:
    
    alpha = pm.Uniform('alpha', lower=0, upper=10)
    beta = pm.Uniform('beta', lower=0, upper=25)
        
    theta = pm.Beta('theta', alpha, beta, shape=rat_tumor.shape[0])
    
    y = pm.Binomial('y', n=rat_tumor[:, 1], p=theta, observed=rat_tumor[:, 0])

model = model_1

# MODELGRAPH:
# nodes:
# 'alpha', 'beta', 'theta', 'y'
# edges:
# 'alpha' -> 'theta'
# 'beta' -> 'theta'
# 'theta' -> 'y'
# END_MODELGRAPH

# NOTE: cannot infer constraint from input