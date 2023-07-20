
using Gen

@gen function model(I:: Bool)
    A ~ bernoulli(0.5)

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


@gen function guide(I:: Bool)
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

