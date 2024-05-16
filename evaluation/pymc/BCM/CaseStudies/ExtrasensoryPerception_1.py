# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/CaseStudies/ExtrasensoryPerception.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt

# Sample size N and effect size E in the Bem experiments
N = np.array([100, 150, 97, 99, 100, 150, 200, 100, 50])
E = np.array([0.25, 0.20, 0.25, 0.20, 0.22, 0.15, 0.09, 0.19, 0.42])

y = np.vstack([N, E]).T
n, n2 = np.shape(y)  # number of experiments

with pm.Model() as model1:
    # r∼Uniform(−1,1)
    r = pm.Uniform("r", lower=-1, upper=1)

    # μ1,μ2∼Gaussian(0,.001)
    mu = pm.Normal("mu", mu=0, tau=0.001, shape=n2)

    # σ1,σ2∼InvSqrtGamma(.001,.001)
    lambda1 = pm.Gamma("lambda1", alpha=0.001, beta=0.001)
    lambda2 = pm.Gamma("lambda2", alpha=0.001, beta=0.001)
    sigma1 = pm.Deterministic("sigma1", 1 / np.sqrt(lambda1))
    sigma2 = pm.Deterministic("sigma2", 1 / np.sqrt(lambda2))

    cov = pm.Deterministic(
        "cov",
        tt.stacklists(
            [[lambda1 ** -1, r * sigma1 * sigma2], [r * sigma1 * sigma2, lambda2 ** -1]]
        ),
    )

    tau1 = pm.Deterministic("tau1", tt.nlinalg.matrix_inverse(cov))

    yd = pm.MvNormal("yd", mu=mu, tau=tau1, observed=y)
    
model = model1

# MODELGRAPH:
# nodes:
# "r", "mu", "lambda1", "lambda2", "sigma1", "sigma2", "cov", "tau1", "yd"
# edges:
# "r" -> "cov"
# "mu" -> "yd"
# "lambda1" -> "cov"
# "lambda2" -> "cov"
# "lambda1" -> "sigma1"
# "lambda2" -> "sigma2"
# "sigma1" -> "cov"
# "sigma2" -> "cov"
# "cov" -> "tau1"
# "tau1" -> "yd"
# END_MODELGRAPH

# NOTE: cannot verify matrix constraint `matrix_inverse(cov)`