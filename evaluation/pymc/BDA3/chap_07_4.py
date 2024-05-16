# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BDA3/chap_07.ipynb

import pymc3 as pm
import theano.tensor as tt
import numpy as np

new_york = np.genfromtxt('data/newyork.txt', skip_header=7, dtype=(int, int))

sample1 = []
sample2 = []

for i, j in new_york[:, :]:
    if j == 400 or j == 200:
        sample1.append(i)
    if j == 300 or j == 200:
        sample2.append(i)
        
sample1.sort()
sample2.sort()

def logp_(value):
    return tt.log(tt.pow(value, -1))

with pm.Model() as model_2:
    mu = pm.Uniform('mu', lower=-5e5, upper=5e5)
    sigma = pm.Uniform('sigma', lower=0, upper=5e5)
    pm.Potential('sigma_log', logp_(sigma))
    y_bar = pm.Normal('y_bar', mu=mu, sd=sigma, observed=sample1)

model = model_2

# MODELGRAPH:
# nodes:
# 'mu', 'sigma', 'y_bar'
# edges:
# 'mu' -> 'y_bar'
# 'sigma' -> 'y_bar'
# END_MODELGRAPH

# NOTE: pymc graph has edge for potential, 'sigma' -> 'sigma_log'