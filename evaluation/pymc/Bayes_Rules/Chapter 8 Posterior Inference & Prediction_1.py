# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# Bayes_Rules/Chapter 8 Posterior Inference & Prediction.ipynb

import pymc3 as pm

num_samples = 5000
n_tune = 5000
n_chains = 4
seed = 84735

with pm.Model() as model:
    p = pm.Beta("p", 4, 6)
    y = pm.Binomial("y", n=100, p=p, observed=14)


model = model

# MODELGRAPH:
# nodes:
# "p", "y"
# edges:
# "p" -> "y"
# END_MODELGRAPH