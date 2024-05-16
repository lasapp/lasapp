# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ModelSelection/ComparingBinomialRates.ipynb

import pymc3 as pm

s1 = 424
s2 = 5416
n1 = 777
n2 = 9072

with pm.Model() as model1:
    theta1 = pm.Beta("theta1", alpha=1, beta=1)
    theta2 = pm.Beta("theta2", alpha=1, beta=1)
    delta = pm.Deterministic("delta", theta1 - theta2)

    s1 = pm.Binomial("s1", p=theta1, n=n1, observed=s1)
    s2 = pm.Binomial("s2", p=theta2, n=n2, observed=s2)

model = model1

# MODELGRAPH:
# nodes:
# "theta1", "theta2", "delta", "s1", "s2"
# edges:
# "theta1" -> "delta"
# "theta2" -> "delta"
# "theta1" -> "s1"
# "theta2" -> "s2"
# END_MODELGRAPH