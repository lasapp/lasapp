import beanmachine.ppl as bm
import torch.distributions as dist
import torch

torch.manual_seed(0)
x = dist.Normal(0., 1.).sample((25,))
y = dist.Normal(2 * x - 1, 1.).sample()

@bm.random_variable
def slope():
    return dist.Normal(0., 10.)

@bm.random_variable
def intercept():
    return dist.Normal(0., 10.)

@bm.random_variable
def sigma():
    return dist.HalfCauchy(1.) #InverseGamma(2., 3.)

@bm.random_variable
def linear_regression(x):
    return dist.Normal(slope() * x + intercept(), sigma())

# observations = {linear_regression(x): y}

observations = {}
observations[linear_regression(x)] = y

model = linear_regression

samples = bm.GlobalHamiltonianMonteCarlo(10).infer(
    queries=[slope(), intercept(), sigma()],
    observations=observations,
    num_samples=5000,
    num_adaptive_samples=500,
    num_chains=1
)

s = samples[slope()].mean()
i = samples[intercept()].mean()
std = samples[sigma()].mean()
print(f"slope: {s:.2f}, intercept: {i:.2f}, sigma: {std:.2f}")
