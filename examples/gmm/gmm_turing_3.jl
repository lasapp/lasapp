
using Turing
import Random
using StatsPlots

Random.seed!(0)
z = (rand(50) .< 0.4) .+ 1
x = (randn(length(z), 2) .* [1 2] .+ [-2 3])[hcat(z .== 1, z .== 2)]

@model function gmm(x)
    p ~ Uniform(0,1)
    
    μ1 ~ Normal(0., 3.)
    μ2 ~ Normal(0., 3.)
    σ²1 ~ InverseGamma(2, 3)
    σ²2 ~ InverseGamma(2, 3)

    z = Vector{Int}(undef, length(x))
    for i in eachindex(x)
        z[i] ~ Bernoulli(p)
        if z[i] == 1
            μ = μ1
            σ² = σ²1
        else
            μ = μ2
            σ² = σ²2
        end

        x[i] ~ Normal(μ, σ²)
    end
end

model = gmm(x)
chain = sample(model, Gibbs(PG(10, :z), HMC(0.05, 10, :μ1, :μ2, :σ²1, :σ²2, :p)), 3_000)

mean(sort(Array(chain[["μ1",  "μ2"]]), dims=2), dims=1)

plot(chain[["μ1",  "μ2"]])