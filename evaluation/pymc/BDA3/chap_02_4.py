# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BDA3/chap_02.ipynb

import pymc3 as pm
import theano.tensor as tt

births = 987
fem_births = 437

central_num = 0.485
width = 0.09

def triangular(central_num, width):
    
    left_num = central_num - width
    right_num = central_num + width
    theta = pm.Triangular('theta', lower=left_num, upper=right_num, c=central_num)
    
#     Comment these lines to see some changes
    if tt.lt(left_num, theta):
        theta = pm.Uniform('theta1', lower=0, upper=left_num)
    if tt.gt(right_num, theta):
        theta = pm.Uniform('theta2', lower=right_num, upper=1)
        
    return theta 


with pm.Model() as model_3:
    theta = triangular(central_num, width)
    obs = pm.Binomial('observed', n=births, p=theta, observed=fem_births)


model = model_3

# MODELGRAPH:
# nodes:
# 'theta', 'theta1', 'theta2', 'observed'
# edges:
# 'theta' -> 'theta1'
# 'theta' -> 'theta2'
# 'theta1' -> 'theta2'
# 'theta' -> 'observed'
# 'theta1' -> 'observed'
# 'theta2' -> 'observed'
# END_MODELGRAPH

# theta in line 22 can be 'theta' or 'theta1'
# theta in line 25 can be 'theta' or 'theta1' or 'theta2'

# NOTE: pymc model graph gets this wrong, because of stochastic branching


# NOTE: cannot do interval arithmetic through function calls yet (RDs)