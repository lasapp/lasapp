# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# Bayes_Rules/Chapter 6.ipynb

import pymc3 as pm

with pm.Model() as beta_binomal_model:
    pi = pm.Beta("beta", 2, 2)
    y = pm.Binomial("y", n=10, p=pi, observed=9)

model = beta_binomal_model

# MODELGRAPH:
# nodes:
# "beta", "y"
# edges:
# "beta" -> "y"
# END_MODELGRAPH
