using Gen
import Random
Random.seed!(0)

@gen function slicing()
    d ~ bernoulli(0.6)
    i ~ bernoulli(0.7)

    if (!i && !d)
        g ~ bernoulli(0.3)
    else
        if (i && !d)
            g ~ bernoulli(0.9)
        else
            g ~ bernoulli(0.5)
        end
    end

    if !i
        s ~ bernoulli(0.2)
    else
        s ~ bernoulli(0.95)
    end

    if !g
        l ~ bernoulli(0.1)
    else
        l ~ bernoulli(0.4)
    end
end

model = slicing
observations = choicemap(:g => false)


traces, log_norm_weights, lml_est = importance_sampling(model, (), observations, 10000)

weights = exp.(log_norm_weights)

for rv in [:d, :i, :s, :l]
    vals = [t[rv] for t in traces]
    mean = vals'weights
    println("$rv mean = $mean")
end