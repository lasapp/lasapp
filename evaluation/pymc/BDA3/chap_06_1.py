# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BDA3/chap_06.ipynb

import pymc3 as pm
import numpy as np
import theano.tensor as tt

numbs = "28 26 33 24 34 -44 27 16 40 -2 29 22 \
24 21 25 30 23 29 31 19 24 20 36 32 36 28 25 21 28 29 \
37 25 28 26 30 32 36 26 30 22 36 23 27 27 28 27 31 27 26 \
33 26 32 32 24 39 28 24 25 32 25 29 27 28 29 16 23"

nums = np.array([int(i) for i in numbs.split(' ')])

def log_p(value):
    return tt.log(tt.pow(value, -2))

with pm.Model() as model_1:
    
    m_s = pm.HalfFlat('m_s', shape=2, testval=np.asarray([10., 10.]))
    pm.Potential('p(a, b)', log_p(m_s))
    
    mu = pm.Deterministic('mu', m_s[0])
    sigma = pm.Deterministic('sigma', m_s[1])
    post = pm.Normal('post', mu=m_s[0], sd=m_s[1], observed=nums)


model = model_1

# MODELGRAPH:
# nodes:
# 'm_s', 'mu', 'sigma', 'post'
# edges:
# 'm_s' -> 'mu'
# 'm_s' -> 'sigma'
# 'm_s' -> 'post'
# END_MODELGRAPH

# NOTE: pymc graph has edge for potential, 'm_s' -> 'p(a, b)'