# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ModelSelection/ComparingBinomialRates.ipynb

import pymc3 as pm
import theano.tensor as tt
import numpy as np

# pledger data:
s1 = 424
s2 = 5416
n1 = 777
n2 = 9072

def phi(x):
    #'Cumulative distribution function for the standard normal distribution'
    return 0.5 + 0.5 * pm.math.erf(x / pm.math.sqrt(2))

def normcdf1(thetap1, thetap2):
    angle = 45 * np.pi / 180
    return phi((np.cos(angle) * thetap1) - (np.sin(angle) * tt.abs_(thetap2)))

def normcdf2(thetap1, thetap2):
    angle = 45 * np.pi / 180
    return phi((np.sin(angle) * thetap1) + (np.cos(angle) * tt.abs_(thetap2)))


with pm.Model() as model2:
    ## the Exact method
    # Adaptation of the exact method as in the book using joint samples from a
    # bivariate standard Gaussian then rotating them by 45 degree. The rotated
    # sample is transform tinto rates that lie in the unit square
    thetap = pm.MvNormal("thetap", mu=[0, 0], tau=pm.math.constant(np.eye(2)), shape=2)

    theta1 = pm.Deterministic("theta1", normcdf1(thetap[0], thetap[1]))
    theta2 = pm.Deterministic("theta2", normcdf2(thetap[0], thetap[1]))

    ## the Approximate method
    # theta2 = pm.Uniform("theta2",lower=0,upper=1)
    # theta1 = pm.Uniform("theta1",lower=0,upper=theta2)

    delta = pm.Deterministic("delta", theta1 - theta2)

    so1 = pm.Binomial("so1", p=theta1, n=n1, observed=s1)
    so2 = pm.Binomial("so2", p=theta2, n=n2, observed=s2)

model = model2

# MODELGRAPH:
# nodes:
# "thetap", "theta1", "theta2", "delta", "so1", "so2"
# edges:
# "thetap" -> "theta1"
# "thetap" -> "theta2"
# "theta1" -> "so1"
# "theta1" -> "delta"
# "theta2" -> "so2"
# "theta2" -> "delta"
# END_MODELGRAPH
