# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ModelSelection/ComparingBinomialRates.ipynb

import pymc3 as pm
import numpy as np
import theano.tensor as tt

def phi(x):
    #'Cumulative distribution function for the standard normal distribution'
    return 0.5 + 0.5 * pm.math.erf(x / pm.math.sqrt(2))

def normcdf1(thetap1, thetap2):
    angle = 45 * np.pi / 180
    return phi((np.cos(angle) * thetap1) - (np.sin(angle) * tt.abs_(thetap2)))

def normcdf2(thetap1, thetap2):
    angle = 45 * np.pi / 180
    return phi((np.sin(angle) * thetap1) + (np.cos(angle) * tt.abs_(thetap2)))

with pm.Model() as modelAE:
    # the Approximate method
    theta2a = pm.Uniform("theta2a", lower=0, upper=1)
    theta1a = pm.Uniform("theta1a", lower=0, upper=theta2a)
    deltaa = pm.Deterministic("deltaa", theta1a - theta2a)

    ## the Exact method
    # Adaptation of the exact method as in the book using joint samples from a
    # bivariate standard Gaussian then rotating them by 45 degree. The rotated
    # sample is transform tinto rates that lie in the unit square
    thetap = pm.MvNormal("thetap", mu=[0, 0], tau=pm.math.constant(np.eye(2)), shape=2)

    theta1e = pm.Deterministic("theta1e", normcdf1(thetap[0], thetap[1]))
    theta2e = pm.Deterministic("theta2e", normcdf2(thetap[0], thetap[1]))

    deltae = pm.Deterministic("deltae", theta1e - theta2e)


model = modelAE

# MODELGRAPH:
# nodes:
# "theta2a", "theta1a", "deltaa", "thetap", "theta1e", "theta2e", "deltae"
# edges:
# "theta2a" -> "theta1a"
# "theta2a" -> "deltaa"
# "theta1a" -> "deltaa"
# "thetap" -> "theta1e"
# "thetap" -> "theta2e"
# "theta1e" -> "deltae"
# "theta2e" -> "deltae"
# END_MODELGRAPH