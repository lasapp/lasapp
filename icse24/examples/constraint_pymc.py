
import numpy as np
import pymc as pm
from pytensor import tensor as at
from pytensor.ifelse import ifelse


with pm.Model() as model:
    b = pm.Bernoulli("b", p=0.99)
    z = pm.Normal("z", mu=0., sigma=1.)
    u = pm.Beta("u", alpha=1, beta=1)
    prob = ifelse(at.eq(b, 1), 1/(1+np.exp(z)), 1.5 * u)
    pm.Geometric("g", p=prob)

# with model:
#     idata = pm.sample(3000, cores=1, random_seed=0)
    # inital draw may fail
    # otherwise prob > 1 will be rejected, but no error

with model:
    idata = pm.sample_prior_predictive(samples=1000, random_seed=0) # will error