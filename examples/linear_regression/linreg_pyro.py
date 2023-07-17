import pyro
import pyro.distributions as dist
from pyro.infer import HMC, MCMC
import torch
from pyro import sample

torch.manual_seed(0)
x = dist.Normal(0., 1.).sample((25,))
y = dist.Normal(2 * x - 1, 1.).sample()

def linear_regression(x, y):
    # Set slope prior.
    slope = pyro.sample("slope", dist.Normal(0., 10.))

    # Set intercept prior.
    intercept = pyro.sample("intercept", dist.Normal(0., 10.))

    # Set variance prior.
    sigma = sample("sigma", dist.InverseGamma(2., 3.))

    for i in range(len(x)):
        pyro.sample(
            f"y[{i}]",
            dist.Normal(slope * x[i] + intercept, sigma), obs=y[i]
            )
        
def linear_regression_2(x, y):
  a = pyro.sample("a", dist.Normal(0,10))
  b = pyro.sample("b", dist.Normal(0,10))
  s2 = pyro.sample("s2", dist.InverseGamma(1,1))

  for i in range(len(x)):
      pyro.sample(f"y_{i}", dist.Normal(a*x[i]+b,s2), obs=y[i])

model = linear_regression_2
hmc_kernel = HMC(model, step_size=0.01, num_steps=10)
mcmc = MCMC(hmc_kernel, num_samples=3000, warmup_steps=1000)
mcmc.run(x, y)

samples = mcmc.get_samples()
slope = samples["slope"]
intercept = samples["intercept"]
std = samples["sigma"]
print(f"slope: {slope.mean():.2f}, intercept: {intercept.mean():.2f}, sigma: {std.mean():.2f}")