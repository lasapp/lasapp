# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BDA3/chap_02.ipynb

import pymc3 as pm

births = 987
fem_births = 437

with pm.Model() as model_2:
    theta = pm.Uniform('theta', lower=0, upper=1)
    trans = pm.Deterministic('trans', pm.logit(theta))
    phi = pm.Deterministic('phi', (1 - theta) / theta)
    obs = pm.Binomial('observed', n=births, p=theta, observed=fem_births)

model = model_2

# MODELGRAPH:
# nodes:
# 'theta', 'trans', 'phi', 'observed'
# edges:
# 'theta' -> 'trans'
# 'theta' -> 'phi'
# 'theta' -> 'observed'
# END_MODELGRAPH