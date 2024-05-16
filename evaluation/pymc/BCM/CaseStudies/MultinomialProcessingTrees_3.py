# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/CaseStudies/MultinomialProcessingTrees.ipynb

import pymc3 as pm
import numpy as np
from theano import tensor as tt
import theano

### Riefer et al (2002) data:
Nsubj = 21
Nitem = 20

response_1=np.array([2,4,4,10,2,1,3,14,2,2,5,11,6,0,4,10,1,
                     0,4,15,1,0,2,17,1,2,4,13,4,1,6,9,5,1,4,
                     10,1,0,9,10,5,0,3,12,0,1,6,13,1,5,7,7,1,
                     1,4,14,2,2,3,13,2,1,5,12,2,0,6,12,1,0,5,
                     14,2,1,8,9,3,0,2,15,1,2,3,14]).reshape(21,-1)
response_2=np.array([7,5,3,5,5,2,3,10,6,2,7,5,9,4,2,5,2,2,7,
                     9,1,3,3,13,5,0,5,10,7,3,4,6,7,3,6,4,4,1,
                     10,5,9,1,2,8,3,1,6,10,3,5,9,3,2,0,6,12,
                     8,0,3,9,3,2,7,8,7,1,5,7,2,1,6,11,5,3,5,
                     7,5,0,6,9,6,2,2,10]).reshape(21,-1)
response_6=np.array([14,3,1,2,12,3,1,4,18,0,1,1,15,3,0,2,7,
                     1,10,2,3,6,11,0,8,4,3,5,17,1,1,1,13,4,
                     3,0,11,6,1,2,16,1,2,1,10,1,3,6,7,13,0,
                     0,8,4,3,5,16,1,1,2,5,4,7,4,15,0,5,0,6,
                     3,6,5,17,2,0,1,17,1,0,2,8,3,6,3]).reshape(21,-1)

kall = [response_1, response_2, response_6]

p = 3
nu = p + 2
Nt = 3


def Phi(x):
    # probit transform
    return 0.5 + 0.5 * pm.math.erf(x / pm.math.sqrt(2))


kshared = theano.shared(kall[0])
with pm.Model() as modelk:
    mu = pm.Normal("mu", mu=0.0, sd=1.0, shape=Nt)
    xi = pm.HalfNormal("xi", sd=1.0, shape=Nt)

    sd_dist = pm.Exponential.dist(1.0)
    packed_chol = pm.LKJCholeskyCov("chol_cov", n=Nt, eta=4, sd_dist=sd_dist)
    # compute the covariance matrix
    chol = pm.expand_packed_triangular(Nt, packed_chol, lower=True)

    vals_raw = pm.Normal("vals_raw", mu=0.0, sd=1.0, shape=(Nt, Nsubj))
    delta = tt.dot(chol, vals_raw).T

    c = Phi(mu[0] + xi[0] * delta[:, 0])
    r = Phi(mu[1] + xi[1] * delta[:, 1])
    u = Phi(mu[2] + xi[2] * delta[:, 2])

    t1 = c * r
    t2 = (1 - c) * (u ** 2)
    t3 = 2 * u * (1 - c) * (1 - u)
    t4 = c * (1 - r) + (1 - c) * (1 - u) ** 2

    muc = pm.Deterministic("muc", Phi(mu[0]))
    mur = pm.Deterministic("mur", Phi(mu[1]))
    muu = pm.Deterministic("muu", Phi(mu[2]))

    p_ = tt.stack([t1, t2, t3, t4])
    kobs = pm.Multinomial("kobs", p=p_.T, n=Nitem, observed=kall[2])
    

model = modelk

# MODELGRAPH:
# nodes:
# "mu", "xi", "chol_cov", "vals_raw", "muc", "mur", "muu", "kobs"
# edges:
# "mu" -> "muc"
# "mu" -> "mur"
# "mu" -> "muu"
# "chol_cov" -> "kobs"
# "vals_raw" -> "kobs"
# "mu" -> "kobs"
# "xi" -> "kobs"
# END_MODELGRAPH


# NOTE: cannot verify simplex constraint