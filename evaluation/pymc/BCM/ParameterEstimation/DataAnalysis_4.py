# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/DataAnalysis.ipynb

import pymc3 as pm
import numpy as np
import pandas as pd

# Load data
dat = pd.read_csv("data/changepointdata.csv")

c = dat.data
n = np.size(c)
sample = np.arange(0, n)

with pm.Model() as model4:
    # μ1,μ2∼Gaussian(0,.001)
    mu = pm.Normal("mu", mu=0, tau=0.001, shape=2)
    # λ∼Gamma(.001,.001)
    lambd = pm.Gamma("lambd", alpha=0.001, beta=0.001)
    # 　τ∼Uniform(0,tmax)
    tau = pm.DiscreteUniform("tau", lower=0, upper=n)

    muvect = pm.math.switch(tau >= sample, mu[0], mu[1])
    cobs = pm.Normal("cobs", mu=muvect, tau=lambd, observed=c)
    
model = model4

# MODELGRAPH:
# nodes:
# "mu", "lambd", "tau", "cobs"
# edges:
# "mu" -> "cobs"
# "lambd" -> "cobs"
# "tau" -> "cobs"
# END_MODELGRAPH