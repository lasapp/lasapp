# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ModelSelection/ComparingGaussianMeans.ipynb

import pymc3 as pm
import numpy as np

# Read data Dr. Smith
Winter = np.array([
    -0.05,0.41,0.17,-0.13,0.00,-0.05,0.00,0.17,0.29,0.04,0.21,0.08,0.37,
            0.17,0.08,-0.04,-0.04,0.04,-0.13,-0.12,0.04,0.21,0.17,0.17,0.17,
            0.33,0.04,0.04,0.04,0.00,0.21,0.13,0.25,-0.05,0.29,0.42,-0.05,0.12,
            0.04,0.25,0.12
])

Summer = np.array([
    0.00,0.38,-0.12,0.12,0.25,0.12,0.13,0.37,0.00,0.50,0.00,0.00,-0.13,
            -0.37,-0.25,-0.12,0.50,0.25,0.13,0.25,0.25,0.38,0.25,0.12,0.00,0.00,
            0.00,0.00,0.25,0.13,-0.25,-0.38,-0.13,-0.25,0.00,0.00,-0.12,0.25,
            0.00,0.50,0.00
])
x = Winter - Summer  # allowed because it is a within-subjects design
x = x / np.std(x) 

with pm.Model() as model2:
    delta1 = pm.HalfCauchy("delta1", beta=1.0)
    delta = pm.Deterministic("delta", -delta1)
    sigma = pm.HalfCauchy("sigma", beta=1.0)

    miu = delta * sigma
    xi = pm.Normal("xi", mu=miu, sd=sigma, observed=x)

model = model2

# MODELGRAPH:
# nodes:
# "delta1", "delta", "sigma", "xi"
# edges:
# "delta1" -> "delta"
# "delta" -> "xi"
# "sigma" -> "xi"
# END_MODELGRAPH