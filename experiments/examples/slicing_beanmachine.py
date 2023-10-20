import beanmachine.ppl as bm
import torch.distributions as dist
import torch
bm.seed(0)

@bm.random_variable
def d():
    return dist.Bernoulli(0.6)

@bm.random_variable
def i():
    return dist.Bernoulli(0.7)

@bm.random_variable
def g():
    if (not i() and not d()):
        return dist.Bernoulli(0.3)
    else:
        if (i() and not d()):
            return dist.Bernoulli(0.9)
        else:
            return dist.Bernoulli(0.5)
        
@bm.random_variable
def s():
    if not i():
        return dist.Bernoulli(0.2)
    else:
        return dist.Bernoulli(0.95)
    

@bm.random_variable
def l():
    if not g():
        return dist.Bernoulli(0.1)
    else:
        return dist.Bernoulli(0.4)
    

observations = {g(): torch.tensor(0.)}
queries = [d(), i(), s(), l()]

samples = bm.SingleSiteAncestralMetropolisHastings().infer(
    queries=queries,
    observations=observations,
    num_samples=10000,
    num_chains=1
)

for rv in queries:
    mean = samples[rv].double().mean()
    print(f"{rv} mean = {mean}")
