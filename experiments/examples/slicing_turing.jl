using Turing
import Random
Random.seed!(0)

@model function slicing(g)
    d ~ Bernoulli(0.6)
    i ~ Bernoulli(0.7)

    if (!i && !d)
        g ~ Bernoulli(0.3)
    else
        if (i && !d)
            g ~ Bernoulli(0.9)
        else
            g ~ Bernoulli(0.5)
        end
    end

    if !i
        s ~ Bernoulli(0.2)
    else
        s ~ Bernoulli(0.95)
    end

    if !g
        l ~ Bernoulli(0.1)
    else
        l ~ Bernoulli(0.4)
    end
end

model = slicing(false)

res = sample(model, IS(), 10000)

weights = exp.(res[:lp]) / sum(exp, res[:lp])

for rv in [:d, :i, :s, :l]
    mean = ((res[rv])'weights)[1]
    println("$rv mean = $mean")
end