# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BDA3/chap_02.ipynb

import pymc3 as pm

births = 987
fem_births = 437

with pm.Model() as model_1:
    theta = pm.Uniform('theta', lower=0, upper=1)
    obs = pm.Binomial('observed', n=births, p=theta, observed=fem_births)


model = model_1

# MODELGRAPH:
# nodes:
# 'theta', 'observed'
# edges:
# 'theta' -> 'observed'
# END_MODELGRAPH