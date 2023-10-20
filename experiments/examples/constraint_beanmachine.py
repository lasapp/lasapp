import beanmachine.ppl as bm
import torch.distributions as dist
import torch
bm.seed(0)

@bm.random_variable
def b():
    return dist.Bernoulli(0.001)

@bm.random_variable
def u():
    return dist.Beta(1,1)

@bm.random_variable
def z():
    return dist.Normal(0,1)
    
@bm.random_variable
def g():
    if b():
        prob = 1/(1+torch.exp(z()))
    else:
        prob = 1.5 * u()
    print("prob", prob.item())
    return dist.Geometric(prob, validate_args=True)

samples = bm.SingleSiteAncestralMetropolisHastings().infer(
    queries=[g()],
    observations={},
    num_samples=5000,
    num_chains=1
) # will error

samples = bm.inference.simulate(
    queries=[g()],
    num_samples=1000
) # will error

