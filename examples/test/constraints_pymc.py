import pymc as pm
with pm.Model() as linear_regression:
    slope = pm.Normal("slope", mu=0., sigma=10.)
    intercept = pm.Normal("intercept", mu=0., sigma=10.)
    sigma = pm.Normal("sigma", mu=0., sigma=1.)

    pm.Normal("y", mu=slope * x + intercept, sigma=sigma, observed=y)

model = linear_regression
