# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/Binomial.ipynb

import pymc3 as pm
import numpy as np

# Data
k = np.array([5])
n = np.array([10])

with pm.Model() as model1:
    # prior
    theta = pm.Beta("theta", alpha=1, beta=1)
    # observed
    x = pm.Binomial("x", n=n, p=theta, observed=k)


model = model1

# MODELGRAPH:
# nodes:
# "theta", "x"
# edges:
# "theta" -> "x"
# END_MODELGRAPH