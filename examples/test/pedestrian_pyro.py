import pyro
import pyro.distributions as dist
import torch

def pedestrian():
    start = pyro.sample("start", dist.Uniform(0, 3))
    t = 0
    position = start
    distance = torch.tensor(0.0)
    while position > 0 and position < 10:
        step = pyro.sample(f"step_{t}", dist.Uniform(-1, 1))
        distance = distance + step.abs()
        position = position + step
        t = t + 1
    pyro.sample("obs", dist.Normal(1.1, 0.1), obs=distance)
    return start


model = pedestrian