import beanmachine.ppl as bm
import torch.distributions as dist
import torch
bm.seed(0)

@bm.random_variable
def state():
    return dist.Categorical(torch.tensor([0.5,0.5]))

@bm.random_variable
def model(n):
    if state() == 1:
        mu = 5.
    else:
        mu = 6.
    return dist.Normal(mu * torch.ones(n), 1.)

X = torch.tensor([4.81, 6.01, 4.62, 6.43, 5.85, 2.63, 6.20, 4.63, 6.02, 7.2])

observations = {model(len(X)): X}

samples = bm.SingleSiteAncestralMetropolisHastings().infer(
    queries=[state()],
    observations=observations,
    num_samples=5000,
    num_chains=1
)

state_mean = samples[state()].double().mean()
print(f"{state_mean=}")


RUN_ERRONEOUS_CODE = False
if RUN_ERRONEOUS_CODE:
    samples = bm.GlobalHamiltonianMonteCarlo(10).infer(
        queries=[state()],
        observations=observations,
        num_samples=5000,
        num_chains=1
    ) # RuntimeError: only Tensors of floating point and complex dtype can require gradients
