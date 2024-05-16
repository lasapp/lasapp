# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/Binomial.ipynb

import pymc3 as pm

# Inferring a Common Rate, With Posterior Predictive
k1 = 2
n1 = 13
k2 = 10
n2 = 10

with pm.Model() as model5:
    # prior
    theta = pm.Beta("theta", alpha=1, beta=1)
    # observed
    x1 = pm.Binomial("x1", n=n2, p=theta, observed=k1)
    x2 = pm.Binomial("x2", n=n2, p=theta, observed=k2)

model = model5

# MODELGRAPH:
# nodes:
# "theta", "x1", "x2"
# edges:
# "theta" -> "x1"
# "theta" -> "x2"
# END_MODELGRAPH