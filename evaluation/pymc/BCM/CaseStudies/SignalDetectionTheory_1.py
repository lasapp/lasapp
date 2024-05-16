# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/CaseStudies/SignalDetectionTheory.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt

#  Load data
dataset = 1
if dataset == 1:  # Demo
    k = 3  # number of cases
    data = np.array([70, 50, 30, 50, 7, 5, 3, 5, 10, 0, 0, 10]).reshape(k, -1)
else:  # Lehrner et al. (1995) data
    k = 3  # number of cases
    data = np.array([148, 29, 32, 151, 150, 40, 30, 140, 150, 51, 40, 139]).reshape(
        k, -1
    )

h = data[:, 0]
f = data[:, 1]
MI = data[:, 2]
CR = data[:, 3]
s = h + MI
n = f + CR

def Phi(x):
    #'Cumulative distribution function for the standard normal distribution'
    # Also it is the probit transform
    return 0.5 + 0.5 * pm.math.erf(x / pm.math.sqrt(2))


with pm.Model() as model1:
    di = pm.Normal("Discriminability", mu=0, tau=0.5, shape=k)
    ci = pm.Normal("Bias", mu=0, tau=2, shape=k)

    thetah = pm.Deterministic("Hit Rate", Phi(di / 2 - ci))
    thetaf = pm.Deterministic("False Alarm Rate", Phi(-di / 2 - ci))

    hi = pm.Binomial("hi", p=thetah, n=s, observed=h)
    fi = pm.Binomial("fi", p=thetaf, n=n, observed=f)

model = model1

# MODELGRAPH:
# nodes:
# "Discriminability", "Bias", "Hit Rate", "False Alarm Rate", "hi", "fi"
# edges:
# "Discriminability" -> "Hit Rate"
# "Discriminability" -> "False Alarm Rate"
# "Bias" -> "Hit Rate"
# "Bias" -> "False Alarm Rate"
# "Hit Rate" -> "hi"
# "False Alarm Rate" -> "fi"
# END_MODELGRAPH