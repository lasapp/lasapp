import pyro
import pyro.distributions as dist
import torch
from pyro.infer import HMC, MCMC
from pyro.infer import Importance, EmpiricalMarginal
torch.manual_seed(0)

def model(X):
    state = pyro.sample("state", dist.Categorical(torch.tensor([0.5,0.5])))
    if state == 1:
        mu = 5.
    else:
        mu = 6.

    pyro.sample("X", dist.Normal(mu * torch.ones(len(X)), 1.), obs=X)

    return state

X = torch.tensor([4.81, 6.01, 4.62, 6.43, 5.85, 2.63, 6.20, 4.63, 6.02, 7.2])


importance = Importance(model, guide=None, num_samples=5000)
importance.run(X)

emp_marginal = EmpiricalMarginal(importance)
weights = importance.get_normalized_weights()
samples = emp_marginal._samples
state_mean = samples.float().dot(weights).item()
print(f"{state_mean=}")


RUN_ERRONEOUS_CODE = False
if RUN_ERRONEOUS_CODE:
    hmc_kernel = HMC(model, step_size=0.01, num_steps=10)
    mcmc = MCMC(hmc_kernel, num_samples=3000, warmup_steps=1000)
    mcmc.run(X) # RuntimeError: Boolean value of Tensor with more than one value is ambiguous (it enumerates state with [0, 1])

