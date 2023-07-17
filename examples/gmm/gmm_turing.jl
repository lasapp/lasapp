
using Turing
import Random

Random.seed!(0)
z = (rand(50) .< 0.4) .+ 1
x = (randn(length(z), 2) .* [1 2] .+ [-2 3])[hcat(z .== 1, z .== 2)]

@model function gmm(x)
    K = 2

    w ~ Dirichlet(K, 1.)
    
    means = Vector{Float64}(undef, K)
    vars = Vector{Float64}(undef, K)
    for k in 1:K
        means[k] ~ Normal(0., 3.)
        vars[k] ~ InverseGamma(2, 3)
    end

    z = Vector{Int}(undef, length(x))
    for i in eachindex(x)
        z[i] ~ Categorical(w)
        x[i] ~ Normal(means[z[i]], sqrt(vars[z[i]]))
    end
end

model = gmm(x)
chain = sample(model, Gibbs(PG(10, :z), HMC(0.05, 10, :means, :vars, :w)), 3_000)
# chain = sample(model, HMC(0.05, 10, :means, :vars, :w, :z), 3_000) # cryptic error

mean(sort(Array(chain[["means[1]",  "means[2]"]]), dims=2), dims=1)