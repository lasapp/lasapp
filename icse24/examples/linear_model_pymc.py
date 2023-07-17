import numpy as np
import pymc as pm

np.random.seed(0)
x = np.random.randn(25)
y = 2 * x - 1 + np.random.randn(25)

with pm.Model() as linear_regression:
    slope = pm.Normal("slope", mu=0., sigma=10.)
    intercept = pm.Normal("intercept", mu=0., sigma=10.)
    sigma = pm.HalfNormal("sigma", sigma=1.)

    pm.Normal("y", mu=slope * x + intercept, sigma=sigma, observed=y)

with pm.Model() as linear_regression_2:
    slope = pm.Normal("slope", mu=0., sigma=10.)
    intercept = pm.Normal("intercept", mu=0., sigma=10.)
    sigma = pm.Normal("sigma", mu=0., sigma=11.) # error

    pm.Normal("y", mu=slope * x + intercept, sigma=sigma, observed=y)


model = linear_regression_2

with linear_regression:
    idata = pm.sample(3000, cores=1, random_seed=0)

    means = idata.posterior.mean()
    slope = means["slope"].values
    intercept = means["intercept"].values
    sigma = means["sigma"].values
    print(f"slope: {slope:.2f}, intercept: {intercept:.2f}, sigma: {sigma:.2f}")


RUN_ERRONEOUS_CODE = False
if RUN_ERRONEOUS_CODE:
    with linear_regression_2:
        idata = pm.sample_prior_predictive(samples=1000, random_seed=0) # will error

graph = pm.model_to_graphviz(linear_regression)
graph.render(directory='tmp', view=True)