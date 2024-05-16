# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BDA3/chap_02.ipynb

import pymc3 as pm

with pm.Model() as poisson_model:
    theta = pm.Gamma('theta', alpha=3, beta=5)
    post = pm.Poisson('post', mu=2 * theta, observed=3)


model = poisson_model

# MODELGRAPH:
# nodes:
# 'theta', 'post'
# edges:
# 'theta' -> 'post'
# END_MODELGRAPH