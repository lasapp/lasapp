using Gen
import Random
Random.seed!(0)

@gen function model()
    b ~ bernoulli(0.99)
    if b
        z ~ normal(0.,1.)
        prob = 1/(1+exp(z))
    else
        u ~ beta(1,1)
        prob = 1.5 * u
    end
    println("prob:", prob)
    g ~ geometric(prob)
end

for i in 1:1000
    generate(model, ()) # will error
end
