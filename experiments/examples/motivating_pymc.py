import numpy as np
import pymc as pm
from pytensor import tensor as at
from pytensor.ifelse import ifelse

X = np.array([4.81, 6.01, 4.62, 6.43, 5.85, 2.63, 6.20, 4.63, 6.02, 7.2])

with pm.Model() as model:
    state = pm.Categorical("state", p = [0.5, 0.5])
    mu = ifelse(at.eq(state, 1), 5., 6.)

    pm.Normal("X", mu=mu, sigma=1, observed=X)

with model:
    idata = pm.sample(3000, cores=1, random_seed=0)

    means = idata.posterior.mean()
    state = means["state"].values
    print(f"state: {state}")


RUN_ERRONEOUS_CODE = False
if RUN_ERRONEOUS_CODE:
    with model:
        step = pm.NUTS([model.state])
        idata = pm.sample(3000, step=[step], cores=1, random_seed=0)
        # ValueError: Can only compute the gradient of continuous types: state
