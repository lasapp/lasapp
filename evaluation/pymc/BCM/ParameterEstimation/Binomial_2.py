# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/Binomial.ipynb

import pymc3 as pm

# data
k1, k2 = 5, 7
n1 = n2 = 10

with pm.Model() as model2:
    # prior
    theta1 = pm.Beta("theta1", alpha=1, beta=1)
    theta2 = pm.Beta("theta2", alpha=1, beta=1)
    # observed
    x1 = pm.Binomial("x1", n=n1, p=theta1, observed=k1)
    x2 = pm.Binomial("x2", n=n2, p=theta2, observed=k2)
    # differences as deterministic
    delta = pm.Deterministic("delta", theta1 - theta2)


model = model2

# MODELGRAPH:
# nodes:
# "theta1", "theta2", "x1", "x2", "delta"
# edges:
# "theta1" -> "x1"
# "theta2" -> "x2"
# "theta1" -> "delta"
# "theta2" -> "delta"
# END_MODELGRAPH