
using Turing
import Random
using StatsPlots

Random.seed!(0)
z = (rand(50) .< 0.4) .+ 1;
x = (randn(length(z), 2) .* [1 2] .+ [-2 3])[hcat(z .== 1, z .== 2)];

histogram(x, normalize=true)
plot!(x -> 0.6*pdf(Normal(-2., 1.), x) + 0.4*pdf(Normal(3., 2.), x), linewidth=3)


@model function gmm(x)
    p ~ Uniform(0,1)         # 0.4
    
    μ1 ~ Normal(0., 3.)      # -2.
    μ2 ~ Normal(0., 3.)      # 3.
    σ²1 ~ InverseGamma(2, 3) # 1.
    σ²2 ~ InverseGamma(2, 3) # 2.

    z = Vector{Float64}(undef, length(x))
    for i in eachindex(x)
        z[i] ~ Uniform(0., 1.)
        if z[i] < p
            x[i] ~ Normal(μ1, sqrt(σ²1))
        else
            x[i] ~ Normal(μ2, sqrt(σ²2))
        end
    end
end

Random.seed!(0)
model = gmm(x)
chain = sample(model, HMC(0.05, 10), 10_000); # does not work well

chain = sample(model, Gibbs(HMC(0.01, 10, :z), HMC(0.05, 10, :μ1, :μ2, :σ²1, :σ²2, :p)), 10_000);

μ_sorted = sort(Array(chain[["μ1",  "μ2"]]), dims=2)
mean(μ_sorted, dims=1)

plot(chain[["μ1",  "μ2"]])
StatsPlots.density(μ_sorted[:,1])
StatsPlots.density(μ_sorted[:,2])



@model function noisy_beta_binomial(x, σ)
    p ~ Beta(2,2)
    z = Vector{Float64}(undef, length(x))
    for i in eachindex(x)
        z[i] ~ Uniform(0., 1.)
        if z[i] < p
            m = 1.
        else
            m = 0.
        end
        x[i] ~ Normal(m, σ)

        # x[i] ~ Bernoulli(p)
    end
end

Random.seed!(0)
p = 0.3
x = Float64.(rand(10) .< p)


σ = 0.1
model = noisy_beta_binomial(x, σ)
# chain = sample(model, NUTS(), 3_000)
chain = sample(model, HMC(0.1, 10), 100_000)

import LinearAlgebra: I
chain = sample(model, MH(I(length(x)+1)*0.1), 100_000)

ps = 0:0.001:1.
posterior = [
    pdf(Beta(2,2), p)*prod(p*pdf(Normal(1.,σ),x[i])+(1-p)*pdf(Normal(0.,σ), x[i]) for i in eachindex(x))
    for p in ps
]
posterior /= (sum(posterior) * (ps[2]-ps[1]))
histogram(chain["p"], normalize=true)
plot!(ps, posterior, linewidth=3)


unnoisy_posterior = Beta(2+sum(x.==1), 2+sum(x.==0))
plot(p -> pdf(unnoisy_posterior, p), xlims=(0,1))
plot!(ps, posterior, linewidth=3)





@model function discontinuous(Y)
    X ~ Uniform(-1,1)
    σ = X > 0. ? 1. : 10.
    Y ~ Normal(0., σ)
end


Random.seed!(0)
model = discontinuous(1.)
chain = sample(model, HMC(0.1, 10), 100)
plot(chain)
plot(chain["acceptance_rate"])
plot!(chain["X"])
# plot!(chain["hamiltonian_energy_error"])

xs = -1:0.001:1

A = pdf(Normal(0., 1.), 1.)
B = pdf(Normal(0., 10.), 1.)
A/(A+B), B/(A+B)


# runtime error depends on first trace
@model function dynamic(Y)
    X ~ Uniform(-1,1)
    if X > 0.
        A ~ Normal(1., 0.1)
        Y ~ Normal(0., abs(A))
    else
        Y ~ Normal(0., 10.)
    end
end

# fails because of discrete
@model function dynamic(Y)
    X ~ Bernoulli(0.5)
    A ~ Normal(1., 0.1)
    if X
        Y ~ Normal(0., abs(A))
    else
        Y ~ Normal(0., 10.)
    end
end

@model function dynamic(Y)
    X ~ Uniform(-1,1)
    A ~ Normal(1., 0.1)
    if X > 0.
        Y ~ Normal(0., abs(A))
    else
        Y ~ Normal(0., 10.)
    end
end

model = dynamic(1.)

chain = sample(model, HMC(0.1, 10), 10_000)
plot(chain)