import pyro
import pyro.distributions as dist
import torch
from pyro.infer import Importance, EmpiricalMarginal
torch.manual_seed(0)

def model(I: bool):
    A = pyro.sample('A', dist.Bernoulli(0.5))

    if A == 1:
        B = pyro.sample('B', dist.Normal(0., 1.))
    else:
        B = pyro.sample('B', dist.Gamma(1, 1))

    if B > 1 and I:
        pyro.sample('C', dist.Beta(1, 1))
    if B < 1 and I:
        pyro.sample('D', dist.Normal(0., 1.))
    if B < 2:
        pyro.sample('D', dist.Normal(0., 2.)) # Duplicated
        pyro.sample('E', dist.Normal(0., 1.))


def guide(I: bool):
    if I:
        A = pyro.sample('A', dist.Bernoulli(0.9))
    else:
        A = pyro.sample('A', dist.Bernoulli(0.1))

    B = pyro.sample('B', dist.Gamma(1, 1)) # Wrong Support

    if B > 1 and I:
        pyro.sample('C', dist.Uniform(0, 1))
    else:
        pyro.sample('D', dist.Normal(0., 1.))
        pyro.sample('E', dist.Normal(0., 1.)) # Not for 1 < B < 2 and I

importance = Importance(model, guide=guide, num_samples=10000)
importance.run(True)
# will error
# once line 20 is removed, will not error but still incompatible guide