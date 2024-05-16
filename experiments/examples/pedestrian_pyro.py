import pyro
import pyro.distributions as dist
import torch
from pyro.infer import HMC, MCMC
from pyro.infer import Importance, EmpiricalMarginal
torch.manual_seed(0)

def pedestrian():
    start = pyro.sample("start", dist.Uniform(0, 3))
    t = 0
    position = start
    distance = torch.tensor(0.0)
    while position > 0 and distance < 10:
        step = pyro.sample(f"step_{t}", dist.Uniform(-1, 1))
        distance = distance + step.abs()
        position = position + step
        t = t + 1
    pyro.sample("obs", dist.Normal(distance, 0.1), obs=1.1)
    return start


model = pedestrian


importance = Importance(model, guide=None, num_samples=5000)
importance.run()

emp_marginal = EmpiricalMarginal(importance)
weights = importance.get_normalized_weights()
samples = emp_marginal._samples
start_mean = samples.float().dot(weights).item()
print(f"IS start mean = {start_mean}")



hmc_kernel = HMC(pedestrian, step_size=0.001, num_steps=10)
mcmc = MCMC(hmc_kernel, num_samples=5000, warmup_steps=0)
mcmc.run()

samples = mcmc.get_samples()
start_mean = samples["start"].mean()
print(f"HMC start mean = {start_mean}")
