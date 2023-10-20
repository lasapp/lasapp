import pyro
import pyro.distributions as dist
import torch
torch.manual_seed(0)

def model():
    b = pyro.sample("b", dist.Bernoulli(0.99))
    if b:
        z = pyro.sample("z", dist.Normal(0.,1.))
        prob = 1/(1+torch.exp(z))
    else:
        u = pyro.sample("u", dist.Beta(1,1))
        prob = 1.5 * u
    
    print("prob:", prob.item())
    pyro.sample("g", dist.Geometric(prob))


for i in range(1000):
    model() # will error