import torch
import pyro.distributions as dist
import matplotlib.pyplot as plt
import pyro
import pyro.infer.mcmc as pyromcmc

def joint_prob(ps: torch.Tensor, n_batch, stride, D_max=10):

    U = 2*torch.rand((n_batch, stride))-1
    X = U.cumsum(dim=1)
    D = U.abs().cumsum(dim=1)
    n_steps_until_distance = (D > D_max).int().argmax(dim=1)
    assert not (D <= D_max).all(dim=1).any()
    print("n_steps_until_distance:", n_steps_until_distance.max().item())
    # print("avg time until exceeded distance", n_steps_until_distance.double().mean().item()) # D_max*2

    prob_est = []
    for p in ps:
        n_steps_until_home = (X > p).int().argmax(dim=1)
        n_steps_until_home[(X <= p).all(dim=1)] = stride

        n_steps = torch.min(n_steps_until_home, n_steps_until_distance)
        distance_at_termination = D[torch.arange(0,n_batch),n_steps]

        # lp_steps = torch.log(torch.tensor(0.5)) * (n_steps + 1)
        lp_distance = dist.Normal(1.1, 0.1).log_prob(distance_at_termination)

        prob_est.append(torch.logsumexp(lp_distance, 0).exp() / n_batch)

    return torch.hstack(prob_est)

torch.manual_seed(1.)
ps = torch.linspace(0,2,100)
prob_true = joint_prob(ps, 10**6, 50, 10)

step_size = ps[1] - ps[0]
prob_true = prob_true / (prob_true.sum() * step_size)

# %%
def pyro_walk_model():
    start = pyro.sample("start", dist.Uniform(0, 3))
    t = 0
    position = start
    distance = torch.tensor(0.0)
    while position > 0 and position < 10:
        step = pyro.sample(f"step_{t}", dist.Uniform(-1, 1))
        distance = distance + torch.abs(step)
        position = position + step
        t = t + 1
    pyro.sample("obs", dist.Normal(1.1, 0.1), obs=distance)
    return start

def pyro_walk_model_step(t, distance, position):
    if not (position > 0 and position < 10):
        return distance
    
    step = pyro.sample(f"step_{t}", dist.Uniform(-1, 1))
    distance = distance + torch.abs(step)
    position = position + step
    return pyro_walk_model_step(t+1, distance, position)

def pyro_walk_model_2():
    start = pyro.sample("start", dist.Uniform(0, 3))
    distance = pyro_walk_model_step(0, start, torch.tensor(0.0))
    pyro.sample("obs", dist.Normal(1.1, 0.1), obs=distance)
    return start

model = pyro_walk_model

kernel = pyromcmc.HMC(
    pyro_walk_model,
    step_size=0.1,
    num_steps=50,
    adapt_step_size=False,
)
torch.manual_seed(0.)
count = 1000
mcmc = pyromcmc.MCMC(kernel, num_samples=count, warmup_steps=count // 10)
mcmc.run()
samples = mcmc.get_samples()

plt.hist(samples['start'], density=True, label="Estimated posterior")
plt.plot(ps, prob_true, label="True posterior")
plt.legend()
plt.show()

torch.manual_seed(0.)
from pyro.infer import Importance, EmpiricalMarginal
importance = Importance(pyro_walk_model, guide=None, num_samples=10**4)
importance.run()

emp_marginal = EmpiricalMarginal(importance)
weights = importance.get_normalized_weights()
samples = emp_marginal._samples

plt.hist(samples, weights=weights, density=True, label="Estimated posterior", bins=30)
plt.plot(ps, prob_true, label="True posterior")
plt.legend()
plt.show()

