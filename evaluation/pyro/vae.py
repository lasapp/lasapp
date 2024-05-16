# Variational Autoencoders
# adapted from
# https://github.com/wonyeol/static-analysis-for-support-match/tree/850fb58ec5ce2f5e82262c2a9bfc067b799297c1/tests/pyro_examples
# vae_model.py + vae_guide.py
# original https://pyro.ai/examples/vae.html
# https://github.com/pyro-ppl/pyro/tree/58080f81b662bd9575cdf4b466ab3d87236c95df/examples/vae/vae.py

import pyro
import pyro.distributions as dist
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import constraints
import pyro.poutine as poutine

def model(x):
    m_fc1 = nn.Linear(50, 400)
    m_fc21 = nn.Linear(400, 784)
    softplus = nn.Softplus()
    sigmoid = nn.Sigmoid()

    x = torch.reshape(x, [256, 784])

    pyro.module("decoder_fc1", m_fc1)
    pyro.module("decoder_fc21", m_fc21)
    with pyro.plate("data", 256): 
        z_loc = torch.zeros([256, 50]) 
        z_scale = torch.ones([256, 50]) 
        z = pyro.sample("latent", dist.Normal(z_loc, z_scale).to_event(1)) 
        hidden = softplus(m_fc1(z)) 
        loc_img = sigmoid(m_fc21(hidden)) 
        pyro.sample("obs", dist.Bernoulli(loc_img).to_event(1), obs=x)

def guide(x):
    g_fc1 = nn.Linear(784, 400)
    g_fc21 = nn.Linear(400, 50)
    g_fc22 = nn.Linear(400, 50)
    softplus = nn.Softplus()

    x = torch.reshape(x, [256, 784]) 

    pyro.module("encoder_fc1", g_fc1)
    pyro.module("encoder_fc21", g_fc21)
    pyro.module("encoder_fc22", g_fc22)
    with pyro.plate("data", 256): 
        hidden = softplus(g_fc1(x)) 
        z_loc = g_fc21(hidden) 
        z_scale = torch.exp(g_fc22(hidden)) 
        pyro.sample("latent", dist.Normal(z_loc, z_scale).to_event(1))