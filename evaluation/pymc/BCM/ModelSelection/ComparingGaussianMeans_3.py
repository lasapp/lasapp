# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ModelSelection/ComparingGaussianMeans.ipynb

import pymc3 as pm
import numpy as np

# Read data
x = np.array(
    [70, 80, 79, 83, 77, 75, 84, 78, 75, 75, 78, 82, 74, 81, 72, 70, 75, 72, 76, 77]
)
y = np.array(
    [56, 80, 63, 62, 67, 71, 68, 76, 79, 67, 76, 74, 67, 70, 62, 65, 72, 72, 69, 71]
)

n1 = len(x)
n2 = len(y)

# Rescale
y = y - np.mean(x)
y = y / np.std(x)
x = (x - np.mean(x)) / np.std(x)

with pm.Model() as model3:
    delta = pm.Cauchy("delta", alpha=0, beta=1)
    mu = pm.Cauchy("mu", alpha=0, beta=1)
    sigma = pm.HalfCauchy("sigma", beta=1)

    alpha = delta * sigma
    xi = pm.Normal("xi", mu=mu + alpha / 2, sd=sigma, observed=x)
    yi = pm.Normal("yi", mu=mu - alpha / 2, sd=sigma, observed=y)
    
model = model3

# MODELGRAPH:
# nodes:
# "delta", "mu", "sigma", "xi", "yi"
# edges:
# "delta" -> "xi"
# "mu" -> "xi"
# "sigma" -> "xi"
# "delta" -> "yi"
# "mu" -> "yi"
# "sigma" -> "yi"
# END_MODELGRAPH