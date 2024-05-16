import beanmachine.ppl as bm
import torch.distributions as dist
import torch
bm.seed(0)

@bm.random_variable
def start():
    return dist.Uniform(0,3)

@bm.random_variable
def step(t):
    return dist.Uniform(-1,1)

@bm.functional
def position(t):
    if t == 0:
        p = start()
    else:
        p = position(t-1) + step(t)
    return p

@bm.functional
def distance(t):
    if t == 0:
        d = torch.tensor(0.)
    else:
        d = distance(t-1) + step(t).abs()
    return d

@bm.random_variable
def end_distance():
    t = 0
    p = start()
    d = torch.tensor(0.0)
    while p > 0 and d < 10:
        t = t + 1
        d = distance(t)
        p = position(t)

    return dist.Normal(d, 0.1)

observations = {end_distance(): torch.tensor(1.1)}


samples = bm.SingleSiteAncestralMetropolisHastings().infer(
    queries=[start()],
    observations=observations,
    num_samples=5000,
    num_chains=1
)

start_mean = samples[start()].double().mean()
print(f"start_mean = {start_mean}")

RUN_ERRONEOUS_CODE = False
if RUN_ERRONEOUS_CODE:
    samples = bm.GlobalHamiltonianMonteCarlo(10, 0.001).infer(
        queries=[start()],
        observations=observations,
        num_samples=1000,
        num_adaptive_samples=0,
        num_chains=1
    ) # takes too long
    start_mean = samples[start()].double().mean()
    print(f"start_mean = {start_mean}")
