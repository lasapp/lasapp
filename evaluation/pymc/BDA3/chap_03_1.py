# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BDA3/chap_03.ipynb

import pymc3 as pm
import numpy as np

numbs = "28 26 33 24 34 -44 27 16 40 -2 29 22 \
24 21 25 30 23 29 31 19 24 20 36 32 36 28 25 21 28 29 \
37 25 28 26 30 32 36 26 30 22 36 23 27 27 28 27 31 27 26 \
33 26 32 32 24 39 28 24 25 32 25 29 27 28 29 16 23"

nums = np.array([int(i) for i in numbs.split(' ')])

with pm.Model() as model_1:
    mu = pm.Uniform('mu', lower=10, upper=30)
    sigma = pm.Uniform('sigma', lower=0, upper=20)
    post = pm.Normal('post', mu=mu, sd=sigma, observed=nums)

model = model_1

# MODELGRAPH:
# nodes:
# 'mu', 'sigma', 'post'
# edges:
# 'mu' -> 'post'
# 'sigma' -> 'post'
# END_MODELGRAPH