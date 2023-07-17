using Gen

@gen function model()
    b ~ bernoulli(0.999)
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

res = generate(model, ());
trace = res[1];

get_choices(trace)
