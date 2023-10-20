using Gen
import Random
Random.seed!(0)

@gen function model(I::Bool)
    A  ~ bernoulli(0.5)

    if A == 1
        B ~ normal(0., 1.)
    else
        B ~ gamma(1, 1)
    end

    if B > 1 && I
        {:C} ~ beta(1, 1)
    end
    if B < 1 && I
        {:D} ~ normal(0., 1.)
    end
    if B < 2
        {:D} ~ normal(0., 2.) # Duplicated
        {:E} ~ normal(0., 1.)
    end
end


@gen function guide(I::Bool)
    if I
        A ~ bernoulli(0.9)
    else
        A ~ bernoulli(0.1)
    end

    B ~ gamma(1, 1) # Wrong Support

    if B > 1 && I
        {:C} ~ uniform_continuous(0, 1)
    else
        {:D} ~ normal(0., 1.)
        {:E} ~ normal(0., 1.) # Not for 1 < B < 2 and I
    end
end


traces, log_norm_weights, lml_est = importance_sampling(model, (true,), choicemap(), guide, (true,), 5000)
# will error
# once line 21 is removed, will not error but still incompatible guide