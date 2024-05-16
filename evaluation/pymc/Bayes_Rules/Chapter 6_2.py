# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# Bayes_Rules/Chapter 6.ipynb

import pymc3 as pm
import numpy as np

with pm.Model() as gamma_poisson_model:
    lambda_ = pm.Gamma("lambda", 3, 1)
    y = pm.Poisson("y", mu=lambda_, observed=np.array([2, 8]))

model = gamma_poisson_model

# MODELGRAPH:
# nodes:
# "lambda", "y"
# edges:
# "lambda" -> "y"
# END_MODELGRAPH