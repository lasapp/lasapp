# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/CaseStudies/SignalDetectionTheory.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt
import pandas as pd

std_d = pd.read_csv("data/heit_rotello_std_d.csv") # deduction data
std_i = pd.read_csv("data/heit_rotello_std_i.csv") # induction data

h1  = np.array(std_i["V1"])
f1  = np.array(std_i["V2"])
MI1 = np.array(std_i["V3"])
CR1 = np.array(std_i["V4"])
s1 = h1 + MI1
n1 = f1 + CR1

h2  = np.array(std_d["V1"])
f2  = np.array(std_d["V2"])
MI2 = np.array(std_d["V3"])
CR2 = np.array(std_d["V4"])
s2 = h2 + MI2
n2 = f2 + CR2

k = len(h1)


def Phi(x):
    #'Cumulative distribution function for the standard normal distribution'
    # Also it is the probit transform
    return 0.5 + 0.5 * pm.math.erf(x / pm.math.sqrt(2))


with pm.Model() as model4d:
    mud = pm.Normal("mud", mu=0, tau=0.001)
    muc = pm.Normal("muc", mu=0, tau=0.001)
    lambdad = pm.Gamma("lambdad", alpha=0.001, beta=0.001)
    lambdac = pm.Gamma("lambdac", alpha=0.001, beta=0.001)

    deltadi = pm.Normal("deltadi", mu=0, sigma=1, shape=k)
    deltaci = pm.Normal("deltaci", mu=0, sigma=1, shape=k)

    sigmad = pm.Deterministic("sigmad", 1 / tt.sqrt(lambdad))
    sigmac = pm.Deterministic("sigmac", 1 / tt.sqrt(lambdac))

    di = pm.Deterministic("di", mud + deltadi / tt.sqrt(lambdad))
    ci = pm.Deterministic("ci", muc + deltaci / tt.sqrt(lambdac))

    thetah = pm.Deterministic("Hit Rate", Phi(di / 2 - ci))
    thetaf = pm.Deterministic("False Alarm Rate", Phi(-di / 2 - ci))

    hi = pm.Binomial("hi", p=thetah, n=s2, observed=h2)
    fi = pm.Binomial("fi", p=thetaf, n=n2, observed=f2)
    
model = model4d

# MODELGRAPH:
# nodes:
# "mud", "muc", "lambdad", "lambdac", "deltadi", "deltaci", "sigmad", "sigmac", "di", "ci", "Hit Rate", "False Alarm Rate", "hi", "fi"
# edges:
# "mud" -> "di"
# "muc" -> "ci"
# "lambdad" -> "sigmad"
# "lambdad" -> "di"
# "lambdac" -> "sigmac"
# "lambdac" -> "ci"
# "deltadi" -> "di"
# "deltaci" -> "ci"
# "di" -> "Hit Rate"
# "di" -> "False Alarm Rate"
# "ci" -> "Hit Rate"
# "ci" -> "False Alarm Rate"
# "Hit Rate" -> "hi"
# "False Alarm Rate" -> "fi"
# END_MODELGRAPH

# NOTE: cannot infer constraints for input s2, n2