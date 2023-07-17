import pyro
import pyro.distributions as dist
import torch
from pyro.infer import Importance, EmpiricalMarginal
torch.manual_seed(0)

def slicing():
    d = pyro.sample("d", dist.Bernoulli(0.6))
    i = pyro.sample("i", dist.Bernoulli(0.7))

    if (not i and not d):
        g = pyro.sample("g", dist.Bernoulli(0.3), obs=torch.tensor(0.))
    else:
        if (i and not d):
            g = pyro.sample("g", dist.Bernoulli(0.9), obs=torch.tensor(0.))
        else:
            g = pyro.sample("g", dist.Bernoulli(0.5), obs=torch.tensor(0.))
      
    if not i:
        s = pyro.sample("s", dist.Bernoulli(0.2))
    else:
        s = pyro.sample("s", dist.Bernoulli(0.95))
    
    if not g:
        l = pyro.sample("l", dist.Bernoulli(0.1))
    else:
        l = pyro.sample("l", dist.Bernoulli(0.4))

    return torch.hstack([d,i,s,l])
    

model = slicing

importance = Importance(model, guide=None, num_samples=10000)
importance.run()

emp_marginal = EmpiricalMarginal(importance)
weights = importance.get_normalized_weights()
samples = emp_marginal._samples
means = weights.matmul(samples.float())
print(f"means of d, i, s, l")
print(means)
