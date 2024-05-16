# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ModelSelection/ComparingBinomialRates.ipynb

import pymc3 as pm
import numpy as np

### Zeelenberg data:
# Study Both:
sb = np.array([
    15,11,15,14,15,18,16,16,18,16,15,13,18,12,11,13,17,18,16,11,17,18,
        12,18,18,14,21,18,17,10,11,12,16,18,17,15,19,12,21,15,16,20,15,19,
        16,16,14,18,16,19,17,11,19,18,16,16,11,19,18,12,15,18,20, 8,12,19,
        16,16,16,12,18,17,11,20
])
nb = 21

# Study Neither:
sn = np.array([
    15,12,14,15,13,14,10,17,13,16,16,10,15,15,10,14,17,18,19,12,19,18,
        10,18,16,13,15,20,13,15,13,14,19,19,19,18,13,12,19,16,14,17,15,16,
        15,16,13,15,14,19,12,11,17,13,18,13,13,19,18,13,13,16,18,14,14,17,
        12,12,16,14,16,18,13,13
])
nn = 21
ns = len(sb)

def phi(x):
    #'Cumulative distribution function for the standard normal distribution'
    return 0.5 + 0.5 * pm.math.erf(x / pm.math.sqrt(2))

with pm.Model() as model3:
    mu = pm.HalfNormal("mu", sd=1)  # standard Gaussian distribution prior. It is known as
    # the "unit information prior", as it carries as much
    # information as a single observation (Kass & Wasserman, 1995)
    sigma = pm.Uniform("sigma", lower=0, upper=10)
    delta = pm.HalfNormal("delta", sd=1)
    sigma_alpha = pm.Uniform("sigma_alpha", lower=0, upper=10)

    mu_alpha = delta * sigma_alpha

    alpha_i = pm.Normal("alpha_i", mu=mu_alpha, sd=sigma_alpha, shape=ns)
    phin = pm.Normal("phin", mu=mu, sd=sigma, shape=ns)

    phib = phin + alpha_i

    thetan = pm.Deterministic("thetan", phi(phin))
    thetab = pm.Deterministic("thetab", phi(phib))

    sno = pm.Binomial("sno", p=thetan, n=nn, observed=sn)
    sbo = pm.Binomial("sbo", p=thetab, n=nb, observed=sb)


model = model3

# MODELGRAPH:
# nodes:
# "mu", "sigma", "delta", "sigma_alpha", "alpha_i", "phin", "thetan", "thetab", "sno", "sbo"
# edges:
# "mu" -> "phin"
# "sigma" -> "phin"
# "delta" -> "alpha_i"
# "sigma_alpha" -> "alpha_i"
# "alpha_i" -> "thetab"
# "phin" -> "thetan"
# "phin" -> "thetab"
# "thetan" -> "sno"
# "thetab" -> "sbo"
# END_MODELGRAPH