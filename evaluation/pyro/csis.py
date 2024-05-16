# Compiled Sequential Importance Sampling
# adapted from
# https://github.com/wonyeol/static-analysis-for-support-match/tree/850fb58ec5ce2f5e82262c2a9bfc067b799297c1/tests/pyro_examples
# csis_model.py + csis_guide.py
# original https://pyro.ai/examples/csis.html
# https://github.com/pyro-ppl/pyro/tree/58080f81b662bd9575cdf4b466ab3d87236c95df/tutorial/source/csis.ipynb

import pyro
import pyro.distributions as dist
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import constraints

observations={"x1": 0, "x2": 0}
def model():
    #########
    # model #
    #########
    prior_mean = torch.tensor(1.)

    obs = torch.tensor([float(observations['x1']),
                        float(observations['x2'])])
    x = pyro.sample("z", dist.Normal(prior_mean, torch.tensor(5**0.5)))
    y1 = pyro.sample("x1", dist.Normal(x, torch.tensor(2**0.5)), obs=obs[0])
    y2 = pyro.sample("x2", dist.Normal(x, torch.tensor(2**0.5)), obs=obs[1])

def guide():
    #########
    # guide #
    #########
    first  = nn.Linear(2, 10)
    second = nn.Linear(10, 20)
    third  = nn.Linear(20, 10)
    fourth = nn.Linear(10, 5)
    fifth  = nn.Linear(5, 2)
    relu = nn.ReLU()

    pyro.module("first", first)
    pyro.module("second", second)
    pyro.module("third", third)
    pyro.module("fourth", fourth)
    pyro.module("fifth", fifth)

    obs = torch.tensor([float(observations['x1']),
                        float(observations['x2'])])
    x1 = obs[0]
    x2 = obs[1]
    v = torch.cat((torch.Tensor.view(x1, [1, 1]),
                torch.Tensor.view(x2, [1, 1])), 1)

    h1  = relu(first(v))
    h2  = relu(second(h1))
    h3  = relu(third(h2))
    h4  = relu(fourth(h3))
    out = fifth(h4)

    mean = out[0, 0]
    std = torch.exp(out[0, 1])
    pyro.sample("z", dist.Normal(mean, std))