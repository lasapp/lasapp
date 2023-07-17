import beanmachine.ppl as bm
import torch.distributions as dist
import torch
bm.seed(0)

torch.manual_seed(0)
x = dist.Normal(0., 1.).sample((25,))
y = dist.Normal(2 * x - 1, 1.).sample()

@bm.random_variable
def slope_2():
    return dist.Normal(0., 10.)

@bm.random_variable
def intercept_2():
    return dist.Normal(0., 10.)

@bm.random_variable
def sigma_2():
    return dist.Normal(0., 1.)

@bm.random_variable
def linear_regression_2(x):
    return dist.Normal(slope_2() * x + intercept_2(), sigma_2(), validate_args=True)

# ----------------------------------------------------------------

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
queries = [slope(), intercept(), sigma()]

samples = bm.GlobalHamiltonianMonteCarlo(10).infer(
    queries=queries,
    observations=observations,
    num_samples=5000,
    num_adaptive_samples=500,
    num_chains=1
)


s = samples[slope()].mean()
i = samples[intercept()].mean()
std = samples[sigma()].mean()
print(f"slope: {s:.2f}, intercept: {i:.2f}, sigma: {std:.2f}")

RUN_ERRONEOUS_CODE = False
if RUN_ERRONEOUS_CODE:
    samples = bm.GlobalHamiltonianMonteCarlo(10).infer(
        queries=[slope_2(), intercept_2(), sigma_2()],
        observations={linear_regression_2(x): y},
        num_samples=5000,
        num_adaptive_samples=500,
        num_chains=1
    ) # will error


x = x[:3]
y = y[:3]
graph = bm.inference.BMGInference().to_graphviz(queries, {linear_regression(x): y})
graph.render(directory='tmp', view=True)