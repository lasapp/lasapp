
using Turing
import Random

Random.seed!(0)
x = randn(25)
y = 2 .* x .- 1 .+ randn(length(x))

@model function linear_regression(x, y)
    # Set slope prior.
    slope ~ Normal(0, sqrt(3))

    # Set intercept prior.
    intercept ~ Normal(0, sqrt(3))

    # Set variance prior.
    σ ~ InverseGamma(2,3)#truncated(Normal(0, 10); lower=0)

    for i in eachindex(x)
        y[i] ~ Normal(intercept + slope * x[i], σ-1)
    end
end

model = linear_regression(x, y)
chain = sample(model, NUTS(0.65), 3_000)

display(mean(chain))
