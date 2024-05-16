# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BDA3/chap_07.ipynb

import pymc3 as pm
import numpy as np
from scipy import stats

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

data_transformed = stats.boxcox(sample2)[0]

with pm.Model() as model_trans_2:
    mu = pm.Uniform('mu', lower=0, upper=1e2)
    sigma = pm.Uniform('sigma', lower=0, upper=5e1)
    y_phi = pm.Normal('y_phi', mu=mu, sd=sigma, observed=data_transformed)


model = model_trans_2

# MODELGRAPH:
# nodes:
# 'mu', 'sigma', 'y_phi'
# edges:
# 'mu' -> 'y_phi'
# 'sigma' -> 'y_phi'
# END_MODELGRAPH