# Sparse Gamma Deep Exponential Family
# adapted from
# https://github.com/wonyeol/static-analysis-for-support-match/tree/850fb58ec5ce2f5e82262c2a9bfc067b799297c1/tests/pyro_examples
# sgdef_model.py + sgdef_guide.py
# original https://pyro.ai/examples/sparse_gamma.html
# https://github.com/pyro-ppl/pyro/tree/58080f81b662bd9575cdf4b466ab3d87236c95df/examples/sparse_gamma_def.py

import pyro
import pyro.distributions as dist
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import constraints
import pyro.poutine as poutine

def model(x):
    #########
    # model #
    #########
    # hyperparams
    alpha_z = torch.tensor(0.1)
    beta_z = torch.tensor(0.1)
    alpha_w = torch.tensor(0.1)
    beta_w = torch.tensor(0.3)

    # model
    x = torch.reshape(x, [320, 4096])

    with pyro.plate("w_top_plate", 4000):
        w_top = pyro.sample("w_top", dist.Gamma(alpha_w, beta_w))
    with pyro.plate("w_mid_plate", 600):
        w_mid = pyro.sample("w_mid", dist.Gamma(alpha_w, beta_w))
    with pyro.plate("w_bottom_plate", 61440):
        w_bottom = pyro.sample("w_bottom", dist.Gamma(alpha_w, beta_w))

    with pyro.plate("data", 320):
        z_top = pyro.sample("z_top", dist.Gamma(alpha_z, beta_z).expand_by([100]).to_event(1))

        w_top = torch.reshape(w_top, [100, 40])
        mean_mid = torch.matmul(z_top, w_top)
        z_mid = pyro.sample("z_mid", dist.Gamma(alpha_z, beta_z / mean_mid).to_event(1))

        w_mid = torch.reshape(w_mid, [40, 15])
        mean_bottom = torch.matmul(z_mid, w_mid)
        z_bottom = pyro.sample("z_bottom", dist.Gamma(alpha_z, beta_z / mean_bottom).to_event(1))

        w_bottom = torch.reshape(w_bottom, [15, 4096])
        mean_obs = torch.matmul(z_bottom, w_bottom)

        pyro.sample('obs', dist.Poisson(mean_obs).to_event(1), obs=x)


def guide(x):
    #########
    # guide #
    #########
    # init params
    alpha_init = 0.5
    mean_init = 0.0
    sigma_init = 0.1
    softplus = nn.Softplus()

    # guide
    x = torch.reshape(x, [320, 4096])

    with pyro.plate("w_top_plate", 4000):
        #============ sample_ws
        alpha_w_q =\
            pyro.param("log_alpha_w_q_top",
                    alpha_init * torch.ones(4000) +
                    sigma_init * torch.randn(4000))
        mean_w_q =\
            pyro.param("log_mean_w_q_top",
                    mean_init * torch.ones(4000) +
                    sigma_init * torch.randn(4000)) 
        alpha_w_q = softplus(alpha_w_q)
        mean_w_q  = softplus(mean_w_q)
        pyro.sample("w_top", dist.Gamma(alpha_w_q, alpha_w_q / mean_w_q))
        #============ sample_ws

    with pyro.plate("w_mid_plate", 600):
        #============ sample_ws
        alpha_w_q =\
            pyro.param("log_alpha_w_q_mid",
                    alpha_init * torch.ones(600) +
                    sigma_init * torch.randn(600)) 
        mean_w_q =\
            pyro.param("log_mean_w_q_mid",
                    mean_init * torch.ones(600) +
                    sigma_init * torch.randn(600)) 
        alpha_w_q = softplus(alpha_w_q)
        mean_w_q  = softplus(mean_w_q)
        pyro.sample("w_mid", dist.Gamma(alpha_w_q, alpha_w_q / mean_w_q))
        #============ sample_ws

    with pyro.plate("w_bottom_plate", 61440):
        #============ sample_ws
        alpha_w_q =\
            pyro.param("log_alpha_w_q_bottom",
                    alpha_init * torch.ones(61440) +
                    sigma_init * torch.randn(61440)) 
        mean_w_q =\
            pyro.param("log_mean_w_q_bottom",
                    mean_init * torch.ones(61440) +
                    sigma_init * torch.randn(61440)) 
        alpha_w_q = softplus(alpha_w_q)
        mean_w_q  = softplus(mean_w_q)
        pyro.sample("w_bottom", dist.Gamma(alpha_w_q, alpha_w_q / mean_w_q))
        #============ sample_ws

    with pyro.plate("data", 320):
        #============ sample_zs
        alpha_z_q =\
            pyro.param("log_alpha_z_q_top",
                    alpha_init * torch.ones(320, 100) +
                    sigma_init * torch.randn(320, 100)) 
        mean_z_q =\
            pyro.param("log_mean_z_q_top",
                    mean_init * torch.ones(320, 100) +
                    sigma_init * torch.randn(320, 100))
        alpha_z_q = softplus(alpha_z_q)
        mean_z_q  = softplus(mean_z_q)
        pyro.sample("z_top", dist.Gamma(alpha_z_q, alpha_z_q / mean_z_q).to_event(1))
        #============ sample_zs
        #============ sample_zs
        alpha_z_q =\
            pyro.param("log_alpha_z_q_mid",
                    alpha_init * torch.ones(320, 40) +
                    sigma_init * torch.randn(320, 40)) 
        mean_z_q =\
            pyro.param("log_mean_z_q_mid",
                    mean_init * torch.ones(320, 40) +
                    sigma_init * torch.randn(320, 40))
        alpha_z_q = softplus(alpha_z_q)
        mean_z_q  = softplus(mean_z_q)
        pyro.sample("z_mid", dist.Gamma(alpha_z_q, alpha_z_q / mean_z_q).to_event(1))
        #============ sample_zs
        #============ sample_zs
        alpha_z_q =\
            pyro.param("log_alpha_z_q_bottom",
                    alpha_init * torch.ones(320, 15) +
                    sigma_init * torch.randn(320, 15)) 
        mean_z_q =\
            pyro.param("log_mean_z_q_bottom",
                    mean_init * torch.ones(320, 15) +
                    sigma_init * torch.randn(320, 15))
        alpha_z_q = softplus(alpha_z_q)
        mean_z_q  = softplus(mean_z_q)
        pyro.sample("z_bottom", dist.Gamma(alpha_z_q, alpha_z_q / mean_z_q).to_event(1))
        #============ sample_zs