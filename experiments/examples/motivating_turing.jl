using Turing
import Random
Random.seed!(0)

@model function model(X)
    state ~ Categorical([0.5, 0.5])
    if state-1 == 1
        mu = 5.
    else
        mu = 6.
    end
    for i in eachindex(X)
        X[i] ~ Normal(mu, 1.)
    end
end

X = [4.81, 6.01, 4.62, 6.43, 5.85, 2.63, 6.20, 4.63, 6.02, 7.2]

res = sample(model(X), IS(), 5000)

weights = exp.(res[:lp]) / sum(exp, res[:lp])

state_mean = ((res[:state].-1)'weights)
state_mean = state_mean[1]
println("state_mean=$state_mean")


RUN_ERRONEOUS_CODE = false
if RUN_ERRONEOUS_CODE
    sample(model(X), HMC(0.1, 10), 3000) # ERROR: LoadError: InexactError: Int64(0.29516513266321925)
end