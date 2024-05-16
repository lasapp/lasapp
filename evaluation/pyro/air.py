# Attend Infer Repeat
# adapted from
# https://github.com/wonyeol/static-analysis-for-support-match/tree/850fb58ec5ce2f5e82262c2a9bfc067b799297c1/tests/pyro_examples
# air_model.py + air_guide.py
# original https://pyro.ai/examples/air.html
# https://github.com/pyro-ppl/pyro/tree/58080f81b662bd9575cdf4b466ab3d87236c95df/examples/air

# %%

import pyro
import pyro.distributions as dist
import torch
import torch.nn as nn
import torch.nn.functional as F

def model(data):
    ###################################
    # vars used in both model & guide #
    ###################################
    expansion_indices = torch.LongTensor([1, 0, 2, 0, 1, 3])
    z_where_loc_prior =\
        nn.Parameter(torch.FloatTensor([3.0, 0.0, 0.0]), requires_grad=False)
    z_where_scale_prior =\
        nn.Parameter(torch.FloatTensor([0.2, 1.0, 1.0]), requires_grad=False)

    #########
    # model #
    #########
    # nn's
    decode_l1 = nn.Linear(50, 200)
    decode_l2 = nn.Linear(200, 784)

    # trial_probs (from z_pres_prior_p)
    z_pres_prior = 0.01
    #===== make_prior
    k = z_pres_prior
    u = 1 / (1 + k + (k*k) + (k*k*k))
    p0 = 1 - u
    p1 = 1 - (k * u) / p0
    p2 = 1 - ((k*k) * u) / (p0 * p1)
    trial_probs = torch.tensor([p0, p1, p2])
    #===== make_prior

    # model()
    data = torch.reshape(data, [60000, 50, 50])

    pyro.module("decode_l1", decode_l1)
    pyro.module("decode_l2", decode_l2)

    with pyro.plate('data', 60000, 64) as ix:
        # size = [64, 50, 50]
        batch = data[ix] 

        #================= prior
        state_x = torch.zeros([64, 50, 50])
        state_z_pres = torch.ones([64, 1])
        state_z_where = None

        z_pres = []
        z_where = []

        for t in range(3):
            #==================== prior_step
            # size = [64, 50, 50]
            prev_x = state_x
            # size = [64, 1]
            prev_z_pres = state_z_pres
            # size = None or [64, 3]
            prev_z_where = state_z_where

            # size = [64, 1]
            cur_z_pres =\
                pyro.sample('z_pres_{}'.format(t),
                            dist.Bernoulli(trial_probs[t] * prev_z_pres)
                            .to_event(1))

            sample_mask = cur_z_pres
            # size = [64, 3]
            cur_z_where =\
                pyro.sample('z_where_{}'.format(t),
                            dist.Normal(torch.Tensor.expand(z_where_loc_prior, [64, 3]),
                                torch.Tensor.expand(z_where_scale_prior, [64, 3]))
                            .mask(sample_mask)
                            .to_event(1))

            # size = [64, 50]
            cur_z_what =\
                pyro.sample('z_what_{}'.format(t),
                            dist.Normal(torch.zeros([64, 50]),
                                torch.ones([64, 50]))
                            .mask(sample_mask)
                            .to_event(1))

            #===== decode
            # size = [64, 784]
            y_att = torch.sigmoid(decode_l2(F.relu(decode_l1(cur_z_what))) - 2.0)
            #===== decode

            #===== window_to_image
            windows = y_att

            #===== expand_z_where
            # size = [64, 4]
            out = torch.cat((torch.zeros(64, 1), cur_z_where), 1)
            # size = [64, 6]
            out = torch.index_select(out, 1, expansion_indices)
            # size = [64, 2, 3]
            out = torch.Tensor.view(out, [64, 2, 3])
            theta = out
            #===== expand_z_where
            # size = [64, 50, 50, 2]
            grid = F.affine_grid(theta, [64, 1, 50, 50])
            # size = [64, 1, 50, 50]
            out = F.grid_sample(torch.Tensor.view(windows, [64, 1, 28, 28]), grid)

            y = torch.Tensor.view(out, [64, 50, 50])
            #===== window_to_image

            # size = [64, 50, 50]
            cur_x = prev_x + (y * torch.Tensor.view(cur_z_pres, [64, 1, 1]))

            state_x = cur_x
            state_z_pres = cur_z_pres
            state_z_where = cur_z_where
            #==================== prior_step

            z_where.append(state_z_where)
            z_pres.append(state_z_pres)

        # size = [64, 50, 50]
        x = state_x
        #================== prior

        pyro.sample('obs',
                    dist.Normal(torch.Tensor.view(x, [64, 2500]),
                        (0.3 * torch.ones(64, 2500)))
                    .to_event(1),
                    obs=torch.Tensor.view(batch, [64, 2500]))

def guide(data):
    ###################################
    # vars used in both model & guide #
    ###################################
    expansion_indices = torch.LongTensor([1, 0, 2, 0, 1, 3])
    z_where_loc_prior =\
        nn.Parameter(torch.FloatTensor([3.0, 0.0, 0.0]), requires_grad=False)
    z_where_scale_prior =\
        nn.Parameter(torch.FloatTensor([0.2, 1.0, 1.0]), requires_grad=False)

    #########
    # guide #
    #########
    # nn's
    rnn = nn.LSTMCell(2554, 256)
    encode_l1 = nn.Linear(784, 200)
    encode_l2 = nn.Linear(200, 100)
    predict_l1 = nn.Linear(256, 200)
    predict_l2 = nn.Linear(200, 7)
    bl_rnn = nn.LSTMCell(2554, 256)
    bl_predict_l1 = nn.Linear(256, 200)
    bl_predict_l2 = nn.Linear(200, 1)

    # param's
    h_init = nn.Parameter(torch.zeros(1, 256))
    c_init = nn.Parameter(torch.zeros(1, 256))
    bl_h_init = nn.Parameter(torch.zeros(1, 256))
    bl_c_init = nn.Parameter(torch.zeros(1, 256))
    z_where_init = nn.Parameter(torch.zeros(1, 3))
    z_what_init = nn.Parameter(torch.zeros(1, 50))

    # guide()
    data = torch.reshape(data, [60000, 50, 50])

    pyro.module('rnn', rnn)
    pyro.module('bl_rnn', bl_rnn)
    pyro.module('predict_l1', predict_l1)
    pyro.module('predict_l2', predict_l2)
    pyro.module('encode_l1', encode_l1)
    pyro.module('encode_l2', encode_l2)
    pyro.module('bl_predict_l1', bl_predict_l1)
    pyro.module('bl_predict_l2', bl_predict_l2)

    pyro.param('h_init', h_init)
    pyro.param('c_init', c_init)
    pyro.param('z_where_init', z_where_init)
    pyro.param('z_what_init', z_what_init)
    pyro.param('bl_h_init', bl_h_init)
    pyro.param('bl_c_init', bl_c_init)

    with pyro.plate('data', 60000, 64) as ix:
        # size = [64, 50, 50]
        batch = data[ix]

        flattened_batch = torch.Tensor.view(batch, [64, 2500])
        # inputs_raw = batch
        # inputs_embed = flattened_batch
        # inputs_bl_embed = flattened_batch

        state_h = torch.Tensor.expand(h_init, [64, 256])
        state_c = torch.Tensor.expand(c_init, [64, 256])
        state_bl_h = torch.Tensor.expand(bl_h_init, [64, 256])
        state_bl_c = torch.Tensor.expand(bl_c_init, [64, 256])
        state_z_pres = torch.ones(64, 1)
        state_z_where = torch.Tensor.expand(z_where_init, [64, 3])
        state_z_what = torch.Tensor.expand(z_what_init, [64, 50])

        z_pres = []
        z_where = []

        for t in range(3):
            #=========== guide_step
            # prev_h = state_h
            # prev_c = state_c
            # prev_bl_h = state_bl_h
            # prev_bl_c = state_bl_c
            # prev_z_pres = state_z_pres
            # prev_z_where = state_z_where
            # prev_z_what = state_z_what

            # size = [64, 2554]
            rnn_input = torch.cat((flattened_batch, state_z_where, state_z_what, state_z_pres), 1)
            # size = [64, 256], [64, 256]
            state_h, state_c = rnn(rnn_input, (state_h, state_c))

            #===== predict
            # size = [64, 7]
            out = predict_l2(F.relu(predict_l1(state_h)))
            # size = [64, 1]
            z_pres_p = torch.sigmoid(out[:, 0:1])
            # size = [64, 3]
            z_where_loc = out[:, 1:4]
            # size = [64, 3]
            z_where_scale = F.softplus(out[:, 4:])
            #===== predict

            #===== baseline_step
            # size = [64, 2554]
            rnn_input = torch.cat((flattened_batch,
                                torch.Tensor.detach(state_z_where),
                                torch.Tensor.detach(state_z_what),
                                torch.Tensor.detach(state_z_pres)), 1)
            # size = [64, 256], [64, 256]
            state_bl_h, state_bl_c = bl_rnn(rnn_input, (state_bl_h, state_bl_c))

            #===== bl_predict
            # size = [64, 1]
            bl_value = bl_predict_l2(F.relu(bl_predict_l1(state_bl_h)))
            #===== bl_predict

            bl_value = bl_value * state_z_pres
            infer_dict = dict(baseline=dict(baseline_value=
                                            torch.squeeze(bl_value, -1)))
            #===== baseline_step

            # size = [64, 1]
            cur_z_pres =\
                pyro.sample('z_pres_{}'.format(t),
                            dist.Bernoulli(z_pres_p * state_z_pres).to_event(1),
                            infer=infer_dict)

            # sample_mask = cur_z_pres
            # size = [64, 3]
            cur_z_where =\
                pyro.sample('z_where_{}'.format(t),
                            dist.Normal(z_where_loc + z_where_loc_prior,
                                z_where_scale * z_where_scale_prior)
                            .mask(cur_z_pres)
                            .to_event(1))

            #===== image_to_window
            # images = batch

            #===== z_where_inv
            # size = [64, 3]
            out = torch.cat((torch.ones(64, 1), -cur_z_where[:, 1:]), 1)
            out = out / cur_z_where[:, 0:1]
            cur_z_where_inv = out
            #===== z_where_inv
            #===== expand_z_where
            # size = [64, 4]
            out = torch.cat((torch.zeros(64, 1), cur_z_where_inv), 1)
            # size = [64, 6]
            out = torch.index_select(out, 1, expansion_indices)
            out = torch.Tensor.view(out, [64, 2, 3])
            theta_inv = out
            #===== expand_z_where

            # size = [64, 28, 28, 2]
            grid = F.affine_grid(theta_inv, [64, 1, 28, 28])
            # size = [64, 1, 28, 28]
            out = F.grid_sample(torch.Tensor.view(batch, [64, 1, 50, 50]), grid)

            x_att = torch.Tensor.view(out, [64, 784])
            #===== image_to_window

            #===== encode
            # size = [64, 100]
            a = encode_l2(F.relu(encode_l1(x_att)))
            # size = [64, 50]
            z_what_loc = a[:, 0:50]
            # size = [64, 50]
            z_what_scale = F.softplus(a[:, 50:])
            #===== encode

            # size = [64, 50]
            cur_z_what =\
                pyro.sample('z_what_{}'.format(t),
                            dist.Normal(z_what_loc, z_what_scale)
                            .mask(cur_z_pres)
                            .to_event(1))

            # state_h = h
            # state_c = c 
            # state_bl_h = bl_h
            # state_bl_c = bl_c
            state_z_pres = cur_z_pres
            state_z_where = cur_z_where
            state_z_what = cur_z_what
            #=========== guide_step

            z_where.append(state_z_where)
            z_pres.append(state_z_pres)

# %%
data = torch.rand([60000, 50, 50])
# %%
pyro.render_model(model, model_args=(data,))
#%%
pyro.render_model(guide, model_args=(data,))
# %%
