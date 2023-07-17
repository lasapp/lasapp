import pyro
import pyro.distributions as dist
import torch
from pyro.infer import HMC, MCMC
torch.manual_seed(0)

x = dist.Normal(0., 1.).sample((25,))
y = dist.Normal(2 * x - 1, 1.).sample()

def linear_model(x, y):
    a = pyro.sample("a", dist.Normal(0,10))
    b = pyro.sample("b", dist.Normal(0,10))
    s2 = pyro.sample("s2", dist.InverseGamma(1,1))

    for i in range(len(x)):
        pyro.sample(f"y_{i}", dist.Normal(a*x[i]+b, s2, validate_args=True), obs=y[i])


def linear_model_2(x, y):
    a = pyro.sample("a", dist.Normal(0,10))
    b = pyro.sample("b", dist.Normal(0,10))
    s2 = pyro.sample("s2", dist.Normal(0,1)) # error
    pyro.sample("y", dist.Normal(a*y+b, s2, validate_args=True), obs=y)

    # for i in range(len(x)):
    #     pyro.sample(f"y_{i}", dist.Normal(a*x[i]+b, s2), obs=y[i])


model = linear_model_2


hmc_kernel = HMC(linear_model, step_size=0.01, num_steps=10)
mcmc = MCMC(hmc_kernel, num_samples=3000, warmup_steps=1000)
mcmc.run(x, y)

samples = mcmc.get_samples()
slope = samples["a"]
intercept = samples["b"]
std = samples["s2"]
print(f"slope: {slope.mean():.2f}, intercept: {intercept.mean():.2f}, sigma: {std.mean():.2f}")


RUN_ERRONEOUS_CODE = False
if RUN_ERRONEOUS_CODE:
    hmc_kernel = HMC(linear_model_2, step_size=0.01, num_steps=10)
    mcmc = MCMC(hmc_kernel, num_samples=3000, warmup_steps=0)
    mcmc.run(x, y) # will error


graph = pyro.render_model(linear_model, model_args=(x[:3],y[:3]))
graph.render(directory='tmp', view=True)