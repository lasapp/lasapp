# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/Binomial.ipynb

import pymc3 as pm

k = 1
n = 15
# Uncomment for Trompetter Data
# k = 24
#  n = 121

with pm.Model() as model_obs:
    theta = pm.Beta("theta", alpha=1, beta=1)
    x = pm.Binomial("x", n=n, p=theta, observed=k)

model = model_obs

# MODELGRAPH:
# nodes:
# "theta", "x"
# edges:
# "theta" -> "x"
# END_MODELGRAPH