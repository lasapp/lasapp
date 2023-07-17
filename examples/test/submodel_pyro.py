
import torch
import torch.distributions as dist
import pyro

# does not work because it is not "SSA"
# def model():
#     a = submodel()
#     return pyro.sample("B", dist.Normal(a, 1.))

# def submodel():
#     return pyro.sample("A", dist.Normal(0., 1.))


def model():
    a = submodel()
    b = pyro.sample("B", dist.Normal(a, 1.))
    return b

def submodel():
    a = pyro.sample("A", dist.Normal(0., 1.))
    c = pyro.sample("C", dist.Normal(0., 1.))
    return a
