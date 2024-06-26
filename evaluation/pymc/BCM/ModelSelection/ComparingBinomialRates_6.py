# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ModelSelection/ComparingBinomialRates.ipynb

import pymc3 as pm
import numpy as np

### Geurts data:
# Normal Controls:
numerrors1 = np.array([
    15,10,61,11,60,44,63,70,57,11,67,21,89,12,63,11,96,10,37,19,44,
                18,78,27,60,14
])
nc         = np.array([
    89,74,128,87,128,121,128,128,128,78,128,106,128,83,128,100,128,
                73,128,86,128,86,128,100,128,79
])
kc         = nc - numerrors1
nsc        = len(kc)
# ADHD:
numerrors2 = np.array([
    88,50,58,17,40,18,21,50,21,69,19,29,11,76,46,36,37,72,27,92,13,
                39,53,31,49,57,17,10,12,21,39,43,49,17,39,13,68,24,21,27,48,54,
                41,75,38,76,21,41,61,24,28,21
])
na         = np.array([
    128,128,128,86,128,117,89,128,110,128,93,107,87,128,128,113,128,
                128,98,128,93,116,128,116,128,128,93,86,86,96,128,128,128,86,128,
                78,128,111,100,95,128,128,128,128,128,128,98,127,128,93,110,96
])
ka         = na - numerrors2
nsa        = len(ka)

def phi(x):
    #'Cumulative distribution function for the standard normal distribution'
    return 0.5 + 0.5 * pm.math.erf(x / pm.math.sqrt(2))


with pm.Model() as model5:
    delta = pm.HalfNormal("delta", sd=1)
    mu_ = pm.Normal("mu", mu=0, sd=1)
    sigma = pm.Uniform("sigma", lower=0, upper=10)
    alpha = delta * sigma

    phic = pm.Normal("phic", mu=mu_ + alpha / 2, sd=sigma, shape=nsc)
    phia = pm.Normal("phia", mu=mu_ - alpha / 2, sd=sigma, shape=nsa)

    thetac = pm.Deterministic("thetac", phi(phic))
    thetaa = pm.Deterministic("thetaa", phi(phia))

    kco = pm.Binomial("kco", p=thetac, n=nc, observed=kc)
    kao = pm.Binomial("kao", p=thetaa, n=na, observed=ka)

model = model5

# MODELGRAPH:
# nodes:
# "delta", "mu", "sigma", "phic", "phia", "thetac", "thetaa", "kco", "kao"
# edges:
# "delta" -> "phic"
# "delta" -> "phia"
# "mu" -> "phic"
# "mu" -> "phia"
# "sigma" -> "phic"
# "sigma" -> "phia"
# "phic" -> "thetac"
# "phia" -> "thetaa"
# "thetac" -> "kco"
# "thetaa" -> "kao"
# END_MODELGRAPH