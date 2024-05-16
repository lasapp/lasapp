# The Semi-Supervised VAE
# adapted from
# https://github.com/wonyeol/static-analysis-for-support-match/tree/850fb58ec5ce2f5e82262c2a9bfc067b799297c1/tests/pyro_examples
# ssvae_model0.py + ssvae_guide0.py
# original http://pyro.ai/examples/ss-vae.html
# https://github.com/pyro-ppl/pyro/tree/58080f81b662bd9575cdf4b466ab3d87236c95df/examples/vae/ss_vae_M2.py

import pyro
import pyro.distributions as dist
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import constraints
import pyro.poutine as poutine

def model():
    # http://pyro.ai/examples/ss-vae.html
    # dist.OneHotCategorical
    # self.decoder.forward
    #
    # - This example does not account for marginalisation over ys.

    xs = torch.rand([200,784])
    ys = None

    softplus = nn.Softplus()
    sigmoid = nn.Sigmoid()

    decoder_fst = nn.Linear(60, 500)
    decoder_fst.weight.data.normal_(0, 0.001)
    decoder_fst.bias.data.normal_(0, 0.001)
    decoder_snd = nn.Linear(500, 784)

    # register this pytorch module and all of its sub-modules with pyro
    pyro.module("decoder_fst", decoder_fst)
    pyro.module("decoder_snd", decoder_snd)

    # batch_size = xs.size(0)
    # batch_size = 200
    # z_dim = 50
    # output_size = 10
    with pyro.plate("data"):
        # sample the handwriting style from the constant prior distribution
        prior_loc = torch.zeros([200, 50])
        prior_scale = torch.ones([200, 50])    
        zs = pyro.sample("z", dist.Normal(prior_loc, prior_scale).to_event(1))

        # if the label y (which digit to write) is supervised, sample from the
        # constant prior, otherwise, observe the value (i.e. score it against the constant prior)
        alpha_prior = torch.ones([200, 10]) / (1.0 * 10)
        if ys is None:
            ys = pyro.sample("y", dist.OneHotCategorical(alpha_prior)) # added
        else:
            ys = pyro.sample("y", dist.OneHotCategorical(alpha_prior), obs=ys)

        # finally, score the image (x) using the handwriting style (z) and
        # the class label y (which digit to write) against the
        # parametrized distribution p(x|y,z) = bernoulli(decoder(y,z))
        # where `decoder` is a neural network       
        hidden = softplus(decoder_fst(torch.cat([zs, ys], 1)))
        loc = sigmoid(decoder_snd(hidden))
        pyro.sample("x", dist.Bernoulli(loc).to_event(1), obs=xs)

        # return loc

def guide():
    # http://pyro.ai/examples/ss-vae.html
    # torch.distributions.OneHotCategorical
    # self.encoder_y.forward, self.encoder_z.forward
    #
    # - This is a simpler version that is not expected to run under TraceEnum_ELBO

    xs = torch.rand([200,784])
    ys = None

    softplus = nn.Softplus()
    softmax = nn.Softmax(dim=-1)

    encoder_y_fst = nn.Linear(784, 500)
    encoder_y_fst.weight.data.normal_(0, 0.001)
    encoder_y_fst.bias.data.normal_(0, 0.001)
    encoder_y_snd = nn.Linear(500, 10)

    encoder_z_fst = nn.Linear(794, 500)
    encoder_z_fst.weight.data.normal_(0, 0.001)
    encoder_z_fst.bias.data.normal_(0, 0.001)
    encoder_z_out1 = nn.Linear(500, 50)
    encoder_z_out2 = nn.Linear(500, 50)

    pyro.module("encoder_y_fst", encoder_y_fst)
    pyro.module("encoder_y_snd", encoder_y_snd)
    pyro.module("encoder_z_fst", encoder_z_fst)
    pyro.module("encoder_z_out1", encoder_z_out1)
    pyro.module("encoder_z_out2", encoder_z_out2)

    # inform Pyro that the variables in the batch of xs, ys are conditionally independent
    with pyro.plate("data"):
        # if the class label (the digit) is not supervised, sample
        # (and score) the digit with the variational distribution
        # q(y|x) = categorical(alpha(x))
        hidden = softplus(encoder_y_fst(xs))
        alpha = softmax(encoder_y_snd(hidden))       
        if ys is None:      
            ys = pyro.sample("y", dist.OneHotCategorical(alpha))
        else:
            ys = pyro.sample("y", dist.OneHotCategorical(alpha), obs=ys) # added

        # sample (and score) the latent handwriting-style with the variational
        # distribution q(z|x,y) = normal(loc(x,y),scale(x,y))
        hidden_z = softplus(encoder_z_fst(torch.cat([xs, ys], -1))) 
        loc = encoder_z_out1(hidden_z) 
        scale = torch.exp(encoder_z_out2(hidden_z))
        pyro.sample("z", dist.Normal(loc, scale).to_event(1))