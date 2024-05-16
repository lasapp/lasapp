# Amortized Latent Dirichlet Allocation
# adapted from
# https://github.com/wonyeol/static-analysis-for-support-match/tree/850fb58ec5ce2f5e82262c2a9bfc067b799297c1/tests/pyro_examples
# lda_model0.py + lda_guide0.py
# original https://pyro.ai/examples/lda.html
# https://github.com/pyro-ppl/pyro/tree/58080f81b662bd9575cdf4b466ab3d87236c95df/examples/lda.py

import pyro
import pyro.distributions as dist
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import constraints

def model(data):
    #########
    # model #
    #########
    # This is a fully generative model of a batch of documents.
    # data is a [num_words_per_doc, num_documents] shaped array of word ids
    # (specifically it is not a histogram). We assume in this simple example
    # that all documents have the same number of words.
    data = torch.reshape(data, [64, 1000])

    # Globals.
    with pyro.plate("topics", 8):
        # shape = [8] + []
        topic_weights = pyro.sample("topic_weights", dist.Gamma(1. / 8, 1.))
        # shape = [8] + [1024]
        topic_words = pyro.sample("topic_words", dist.Dirichlet(torch.ones(1024) / 1024))

    # Locals.
    # with pyro.plate("documents", 1000) as ind:
    with pyro.plate("documents", 1000, 32, dim=-1) as ind:
        # if data is not None:
        #     data = data[:, ind]
        # shape = [64, 32]
        data = data[:, ind]
        # shape = [32] + [8]
        doc_topics = pyro.sample("doc_topics", dist.Dirichlet(topic_weights))

        with pyro.plate("words", 64, dim=-2):
            # The word_topics variable is marginalized out during inference,
            # achieved by specifying infer={"enumerate": "parallel"} and using
            # TraceEnum_ELBO for inference. Thus we can ignore this variable in
            # the guide.
            # shape = [64, 32] + []
            word_topics =\
                pyro.sample("word_topics", dist.Categorical(doc_topics),
                            infer={"enumerate": "parallel"})
            # shape = [64, 32] + []
            data =\
                pyro.sample("doc_words", dist.Categorical(topic_words[word_topics]),
                            obs=data)
            
def guide(data):
    #########
    # guide #
    #########
    # nn
    layer1 = nn.Linear(1024,100)
    layer2 = nn.Linear(100,100)
    layer3 = nn.Linear(100,8)
    sigmoid = nn.Sigmoid()

    layer1.weight.data.normal_(0, 0.001)
    layer1.bias.data.normal_(0, 0.001)
    layer2.weight.data.normal_(0, 0.001)
    layer2.bias.data.normal_(0, 0.001)
    layer3.weight.data.normal_(0, 0.001)
    layer3.bias.data.normal_(0, 0.001)

    # guide
    data = torch.reshape(data, [64, 1000])

    pyro.module("layer1", layer1)
    pyro.module("layer2", layer2)
    pyro.module("layer3", layer3)

    # Use a conjugate guide for global variables.
    topic_weights_posterior = pyro.param(
        "topic_weights_posterior",
        # lambda: torch.ones(8) / 8,
        torch.ones(8) / 8,
        constraint=constraints.positive)
    topic_words_posterior = pyro.param(
        "topic_words_posterior",
        # lambda: torch.ones(8, 1024) / 1024,
        torch.ones(8, 1024) / 1024,
        constraint=constraints.positive)

    with pyro.plate("topics", 8):
        # shape = [8] + []
        topic_weights = pyro.sample("topic_weights", dist.Gamma(topic_weights_posterior, 1.))
        # shape = [8] + [1024]
        topic_words = pyro.sample("topic_words", dist.Dirichlet(topic_words_posterior))

    # Use an amortized guide for local variables.
    with pyro.plate("documents", 1000, 32) as ind:
        # shape =  [64, 32]
        data = data[:, ind]
        # The neural network will operate on histograms rather than word
        # index vectors, so we'll convert the raw data to a histogram.
        counts = torch.zeros(1024, 32)
        counts = torch.Tensor.scatter_add_\
            (counts, 0, data,
            torch.Tensor.expand(torch.tensor(1.), [1024, 32]))
        h1 = sigmoid(layer1(torch.transpose(counts, 0, 1)))
        h2 = sigmoid(layer2(h1))
        # shape = [32, 8]
        doc_topics_w = sigmoid(layer3(h2))
        # shape = [32] + [8]
        doc_topics = pyro.sample("doc_topics", dist.Delta(doc_topics_w).to_event(1)) # "BUG"

# NOTE: doc_topics has Delta distribution in guide, but Dirichlet distribution in model
# NOTE: word_topics is missing from guide