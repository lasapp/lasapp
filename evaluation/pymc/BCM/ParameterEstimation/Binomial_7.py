# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/Binomial.ipynb

import pymc3 as pm
import numpy as np

k = np.array([16, 18, 22, 25, 27])
nmax = 500

with pm.Model() as model6_:
    # prior
    theta = pm.Beta("theta", alpha=1, beta=1)
    TotalN = pm.Uniform("TotalN", lower=1, upper=nmax)
    # observed
    x = pm.Binomial("x", n=TotalN, p=theta, observed=k)

model = model6_

# MODELGRAPH:
# nodes:
# "theta", "TotalN", "x"
# edges:
# "theta" -> "x"
# "TotalN" -> "x"
# END_MODELGRAPH