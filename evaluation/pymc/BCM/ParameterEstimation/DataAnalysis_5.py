# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/DataAnalysis.ipynb

import pymc3 as pm
import numpy as np

n = 50  # Number of questions
nfails = 949
unobsmin = 15
unobsmax = 25
unobsrange = np.arange(unobsmin, unobsmax + 1)
z = 30

def CensorLike(n, p, unobsrange, nfails):
    # The log likelihood of the unobserved zs is given by the
    # log CDF of the Binomial distribution within the unobsrange 
    # multiplied by the number of failures
    binom = pm.Binomial.dist(n=n, p=p)
    return binom.logp(unobsrange).sum() * nfails        

with pm.Model() as model5:
    theta = pm.Uniform("theta", lower=0.25, upper=1)

    unobs = pm.Potential("unobs", CensorLike(n, theta, unobsrange, nfails))
    obs = pm.Binomial("obs", n=n, p=theta, observed=z)
    
model = model5

# MODELGRAPH:
# nodes:
# "theta", "obs"
# edges:
# "theta" -> "obs"
# END_MODELGRAPH

# NOTE: pymc graph has edge for potential, "theta" -> "unobs"