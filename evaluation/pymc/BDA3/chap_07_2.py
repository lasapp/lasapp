# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BDA3/chap_07.ipynb

import pymc3 as pm
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

with pm.Model() as model_1_log:
    mu = pm.Uniform('mu', lower=0, upper=5e2)
    sigma = pm.Uniform('sigma', lower=0, upper=5e2)
#     pm.Potential('simga_log', logp_(sigma))
    y_bar = pm.Lognormal('y_bar', mu=mu, sd=sigma, observed=sample1)


model = model_1_log

# MODELGRAPH:
# nodes:
# 'mu', 'sigma', 'y_bar'
# edges:
# 'mu' -> 'y_bar'
# 'sigma' -> 'y_bar'
# END_MODELGRAPH
