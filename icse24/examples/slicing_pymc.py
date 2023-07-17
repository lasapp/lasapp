
import numpy as np
import pymc as pm
from pytensor import tensor as at
from pytensor.ifelse import ifelse


with pm.Model() as model:
    d = pm.Bernoulli("d", p=0.6)
    i = pm.Bernoulli("i", p=0.7)

    g_prob = ifelse(at.eq(i,0) & at.eq(d,0),
               np.float32(0.3), 
               ifelse(at.eq(i,1) & at.eq(d,0),
                      np.float32(0.9),
                      np.float32(0.5)
                      )
                )
    g = pm.Bernoulli("g", p=g_prob, observed=0)
      
    s_prob = ifelse(at.eq(i,0), np.float32(0.2), np.float32(0.95))
    s = pm.Bernoulli("s", p=s_prob)
    
    l_prob = ifelse(at.eq(g,0), np.float32(0.1), np.float32(0.4))
    l = pm.Bernoulli("l", p=l_prob)
    


with model:
    idata = pm.sample(10000, cores=1, random_seed=0)

    means = idata.posterior.mean()
    
    for rv in ["d", "i", "s", "l"]:
        mean = means[rv].values
        print(f"{rv} mean = {mean}")