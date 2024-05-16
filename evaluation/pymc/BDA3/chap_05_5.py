# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BDA3/chap_05.ipynb

import pymc3 as pm
import numpy as np

yy = np.array([28.,  8., -3.,  7., -1.,  1., 18., 12.])
sigma = np.array([15., 10., 16., 11.,  9., 11., 10., 18.])

with pm.Model() as model_4:
    mu = pm.Uniform('mu', lower=0, upper=30)
    tau_sq = pm.InverseGamma('tau_sq', 0.001, 0.001)
#     tau = pm.Deterministic('tau', pm.math.sqrt(tau_sq))
    theta = pm.Normal('theta', mu=mu, sd=tau_sq, shape=yy.shape[0])
    obs = pm.Normal('obs', mu=theta, sd=sigma, observed=yy)

model = model_4

# MODELGRAPH:
# nodes:
# 'mu', 'tau_sq', 'theta', 'obs'
# edges:
# 'mu' -> 'theta'
# 'tau_sq' -> 'theta'
# 'theta' -> 'obs'
# END_MODELGRAPH