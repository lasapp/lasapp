using Turing
import Random
Random.seed!(0)

@model function model()
    b ~ Bernoulli(0.99)
    if b
        z ~ Normal(0.,1.)
        prob = 1/(1+exp(z))
    else
        u ~ Beta(1,1)
        prob = 1.5 * u
    end
    println("prob:", prob)
    g ~ Geometric(prob)
end

sample(model(), Prior(), 1000) # will error
