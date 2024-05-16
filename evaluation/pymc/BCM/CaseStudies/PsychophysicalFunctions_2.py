# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/CaseStudies/PsychophysicalFunctions.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt
import pandas as pd

x = pd.read_csv("./data/data_x.txt", sep="\t", header=None)
n = pd.read_csv("./data/data_n.txt", sep="\t", header=None)
r = pd.read_csv("./data/data_r.txt", sep="\t", header=None)
rprop = pd.read_csv("./data/data_rprop.txt", sep="\t", header=None)

xmean = np.array(
    [318.888, 311.0417, 284.4444, 301.5909, 296.2000, 305.7692, 294.6429, 280.3571]
)
nstim = np.array([27, 24, 27, 22, 25, 26, 28, 28])
nsubjs = 8

xij_tmp = x.values
nij_tmp = n.values
rij_tmp = r.values
tmp, nstim2 = np.shape(xij_tmp)

xmeanvect = np.repeat(xmean, nstim2)
sbjidx = np.repeat(np.arange(nsubjs), nstim2)

# remove nans
validmask = np.isnan(xij_tmp.flatten()) == False
xij2 = xij_tmp.flatten()
nij2 = nij_tmp.flatten()
rij2 = rij_tmp.flatten()

xij = xij2[validmask]
nij = nij2[validmask]
rij = rij2[validmask]
xvect = xmeanvect[validmask]
sbjid = sbjidx[validmask]

def Phi(x):
    # probit transform
    return 0.5 + 0.5 * pm.math.erf(x / pm.math.sqrt(2))


def tlogit(x):
    return 1 / (1 + tt.exp(-x))

with pm.Model() as model2b:
    sigma_a = pm.Uniform("sigma_a", lower=0, upper=1000)
    sigma_b = pm.Uniform("sigma_b", lower=0, upper=1000)
    mu_a = pm.Normal("mu_a", mu=0, tau=0.001)
    mu_b = pm.Normal("mu_b", mu=0, tau=0.001)
    alpha = pm.Normal("alpha", mu=mu_a, sd=sigma_a, shape=nsubjs)
    beta = pm.Normal("beta", mu=mu_b, sd=sigma_b, shape=nsubjs)

    linerpredi = alpha[sbjid] + beta[sbjid] * (xij - xvect)

    # latent model for contamination
    sigma_p = pm.Uniform("sigma_p", lower=0, upper=3)
    mu_p = pm.Normal("mu_p", mu=0, tau=0.001)

    probitphi = pm.Normal(
        "probitphi", mu=mu_p, sd=sigma_p, shape=nsubjs, testval=np.ones(nsubjs)
    )
    phii = pm.Deterministic("phii", Phi(probitphi))

    pi_ij = pm.Uniform("pi_ij", lower=0, upper=1, shape=xij.shape)

    # reparameterized so we can use ADVI initialization
    # zij_ = pm.Uniform('zij_',lower=0, upper=1, shape=xij.shape)
    # zij = pm.Deterministic('zij', tt.lt(zij_, phii[sbjid]))

    # rng = tt.shared_randomstreams.RandomStreams()
    # zij_ = rng.binomial(n=1, p=phii[sbjid], size=xij.shape)
    zij_ = pm.theanof.tt_rng().uniform(size=xij.shape)
    zij = pm.Deterministic("zij", tt.lt(zij_, phii[sbjid]))
    # zij = pm.Deterministic('zij', tt.eq(zij_, 0))

    thetaij = pm.Deterministic("thetaij", tt.switch(zij, tlogit(linerpredi), pi_ij))

    rij_ = pm.Binomial("rij", p=thetaij, n=nij, observed=rij)

model = model2b

# MODELGRAPH:
# nodes:
# "sigma_a", "sigma_b", "mu_a", "mu_b", "alpha", "beta", "sigma_p", "mu_p", "probitphi", "phii", "pi_ij", "zij", "thetaij", "rij"
# edges:
# "sigma_a" -> "alpha"
# "mu_a" -> "alpha"
# "sigma_b" -> "beta"
# "mu_b" -> "beta"
# "alpha" -> "thetaij"
# "beta" -> "thetaij"
# "thetaij" -> "rij"
# "sigma_p" -> "probitphi"
# "mu_p" -> "probitphi"
# "probitphi" -> "phii"
# "phii" -> "zij"
# "pi_ij" -> "thetaij"
# "zij" -> "thetaij"
# "thetaij" -> "rij"
# END_MODELGRAPH


# NOTE: cannot infer constraints for input nij