# Bayesian Regression - Inference Algorithms (Part 2)
# adapted from
# https://github.com/wonyeol/static-analysis-for-support-match/tree/850fb58ec5ce2f5e82262c2a9bfc067b799297c1/tests/pyro_examples
# br_guide0.py + br_model0.py
# original https://pyro.ai/examples/bayesian_regression_ii.html
# https://github.com/pyro-ppl/pyro/tree/58080f81b662bd9575cdf4b466ab3d87236c95df/tutorial/source/bayesian_regression_ii.ipynb

import pyro
import pyro.distributions as dist
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import constraints

def model():
    # Non-deterministic initialisation artifically added to help the analysis
    is_cont_africa = torch.rand([170])
    ruggedness = torch.rand([170])
    log_gdp = torch.rand([170])

    # Non-deterministic initialisation
    a = pyro.sample("a", dist.Normal(8., 1000.))
    b_a = pyro.sample("bA", dist.Normal(0., 1.))
    b_r = pyro.sample("bR", dist.Normal(0., 1.))
    b_ar = pyro.sample("bAR", dist.Normal(0., 1.))
    sigma = pyro.sample("sigma", dist.Uniform(0., 10.))
    mean = a + b_a * is_cont_africa + b_r * ruggedness + b_ar * is_cont_africa * ruggedness 
    with pyro.plate("data", 170):
        pyro.sample("obs", dist.Normal(mean, sigma), obs=log_gdp)

def guide():
    is_cont_africa = torch.rand([170])
    ruggedness = torch.rand([170])
    log_gdp = torch.rand([170])

    # Actual code
    a_loc = pyro.param('a_loc', torch.tensor(0.))
    a_scale = pyro.param('a_scale', torch.tensor(1.), constraint=constraints.positive)
    sigma_loc = pyro.param('sigma_loc', torch.tensor(1.), constraint=constraints.positive)
    weights_loc = pyro.param('weights_loc', torch.rand(3))
    weights_scale = pyro.param('weights_scale', torch.ones(3), constraint=constraints.positive)
    a = pyro.sample("a", dist.Normal(a_loc, a_scale))
    b_a = pyro.sample("bA", dist.Normal(weights_loc[0], weights_scale[0]))
    b_r = pyro.sample("bR", dist.Normal(weights_loc[1], weights_scale[1]))
    b_ar = pyro.sample("bAR", dist.Normal(weights_loc[2], weights_scale[2]))
    sigma = pyro.sample("sigma", dist.Normal(sigma_loc, torch.tensor(0.05))) # BUG
    # sigma = pyro.sample("sigma", dist.Uniform(0.1, 10.)) # FIX
    mean = a + b_a * is_cont_africa + b_r * ruggedness + b_ar * is_cont_africa * ruggedness

# NOTE: sigma has Normal distribution in guide, but uniform(0,10) distribution in model