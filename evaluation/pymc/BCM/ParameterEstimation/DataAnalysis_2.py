# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/DataAnalysis.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt

# The datasets:
y = np.array(
    [
        0.8,
        102,
        1,
        98,
        0.5,
        100,
        0.9,
        105,
        0.7,
        103,
        0.4,
        110,
        1.2,
        99,
        1.4,
        87,
        0.6,
        113,
        1.1,
        89,
        1.3,
        93,
    ]
).reshape((11, 2))
# y = np.array([.8,102, 1,98, .5,100, 0.9,105, .7,103,
#                0.4,110, 1.2,99, 1.4,87, 0.6,113, 1.1,89, 1.3,93,
#                .8,102, 1,98, .5,100, 0.9,105, .7,103,
#                0.4,110, 1.2,99, 1.4,87, 0.6,113, 1.1,89, 1.3,93]).reshape((22, 2))

n1, n2 = np.shape(y)
sigmaerror = np.array([0.03, 1])
se = np.tile(sigmaerror, (n1, 1))

with pm.Model() as model2:
    #  r∼Uniform(−1,1)
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

    # xi∼MvGaussian((μ1,μ2),[σ1^2,rσ1σ2;rσ1σ2,σ2^2]^−1)
    yd = pm.MvNormal("yd", mu=mu, cov=cov, shape=(n1, n2))

    xi = pm.Normal("xi", mu=yd, sd=sigmaerror, observed=y)

model = model2

# MODELGRAPH:
# nodes:
# "r", "mu", "lambda1", "lambda2", "sigma1", "sigma2", "cov", "yd", "xi"
# edges:
# "r" -> "cov"
# "mu" -> "yd"
# "lambda1" -> "sigma1"
# "lambda1" -> "cov"
# "lambda2" -> "sigma2"
# "lambda2" -> "cov"
# "sigma1" -> "cov"
# "sigma2" -> "cov"
# "cov" -> "yd"
# "yd" -> "xi"
# END_MODELGRAPH

# NOTE: cannot verify covariance constraint