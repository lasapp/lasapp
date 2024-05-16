# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102
# BCM/ParameterEstimation/DataAnalysis.ipynb

import pymc3 as pm

x = 10  # number of captures
k = 4  # number of recaptures from n
n = 5  # size of second sample
tmax = 50  # maximum population size

betaln = pm.distributions.dist_math.betaln

def HyperGeometric(N, k, n):
    def logp(value):
        # Log likelihood of the HyperGeometric distribution
        tot, good = N, k
        bad = tot - good
        result = (
            betaln(good + 1, 1)
            + betaln(bad + 1, 1)
            + betaln(tot - n + 1, n + 1)
            - betaln(value + 1, good - value + 1)
            - betaln(n - value + 1, bad - n + value + 1)
            - betaln(tot + 1, 1)
        )
        return result
    return logp

with pm.Model() as model7:
    tau = pm.DiscreteUniform("tau", lower=x + (n - k), upper=tmax)
    obs = pm.DensityDist("obs", HyperGeometric(tau, x, n), observed=k)

model = model7

# MODELGRAPH:
# nodes:
# "tau", "obs"
# edges:
# "tau" -> "obs"
# END_MODELGRAPH


# NOTE: DensityDist