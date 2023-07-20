import numpy as np
import pymc as pm

np.random.seed(0)
x = np.random.randn(25)
y = 2 * x - 1 + np.random.randn(25)

with pm.Model() as linear_regression:
    # Set slope prior.
    slope = pm.Normal("slope", mu=0., sigma=10.)

    # Set intercept prior.
    intercept = pm.Normal("intercept", mu=0., sigma=10.)

    # Set variance prior.
    sigma = pm.HalfNormal("sigma", sigma=1.)

    pm.Normal("y", mu=slope * x + intercept, sigma=sigma, observed=y)

model = linear_regression

with model:
    # draw 3000 posterior samples
    idata = pm.sample(3000, cores=1, random_seed=0)

    means = idata.posterior.mean()
    slope = means["slope"].values
    intercept = means["intercept"].values
    std = means["sigma"].values
    print(f"slope: {slope:.2f}, intercept: {intercept:.2f}, std: {std:.2f}")

