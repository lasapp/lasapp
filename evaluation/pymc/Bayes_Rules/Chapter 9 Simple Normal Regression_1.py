# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# Bayes_Rules/Chapter 9 Simple Normal Regression.ipynb

import pymc3 as pm
import numpy as np
import pyreadr

data = pyreadr.read_r("data/bikes.rda")
data = data["bikes"]


with pm.Model() as simple_normal_model:
    beta_0 = pm.Normal("intercept", 5000, 1000)
    beta_1 = pm.Normal("beta", 100, 400)
    sigma = pm.Exponential("sigma", 0.0008)
    y = pm.Normal(
        "y",
        mu=beta_0 + beta_1 * np.asarray(data["temp_feel"]),
        sigma=sigma,
        observed=data["rides"],
    )

model = simple_normal_model

# MODELGRAPH:
# nodes:
# "intercept", "beta", "sigma", "y"
# edges:
# "intercept" -> "y"
# "beta" -> "y"
# "sigma" -> "y"
# END_MODELGRAPH