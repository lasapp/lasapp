# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BDA3/chap_05.ipynb

import pymc3 as pm
import numpy as np
import theano.tensor as tt

rat_tumor = np.loadtxt('data/rat_tumor_data.txt', skiprows=3)

def logp_ab(value):
    """
    Prior density for this problem
    """
    return tt.log(tt.pow(tt.sum(value), -5/2))

with pm.Model() as model_10:
    # Proper noninformative prior for alpha and beta
    ab = pm.HalfFlat('ab', shape=2, testval=np.asarray([1., 1.]))
    pm.Potential('p(a, b)', logp_ab(ab))
    
    # Our alpha and beta
    alpha = pm.Deterministic('alpha', ab[0])
    beta = pm.Deterministic('beta', ab[1])
    
    theta = pm.Beta('theta', alpha=ab[0], beta=ab[1], shape=rat_tumor.shape[0])

    p = pm.Binomial('y', p=theta, observed=rat_tumor[:,0], n=rat_tumor[:,1])


model = model_10

# MODELGRAPH:
# nodes:
# 'ab', 'alpha', 'beta', 'theta', 'y'
# edges:
# 'ab' -> 'alpha'
# 'ab' -> 'beta'
# 'ab' -> 'theta'
# 'theta' -> 'y'
# END_MODELGRAPH

# NOTE: pymc graph has edge for potential, 'ab' -> 'p(a, b)'
# NOTE: cannot infer constraint from input