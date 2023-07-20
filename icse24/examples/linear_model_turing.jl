using Turing
import Random
Random.seed!(0)

x = randn(25)
y = 2 .* x .- 1 .+ randn(length(x))

@model function linear_regression(x, y)
    slope ~ Normal(0, 10)
    intercept ~ Normal(0, 10)
    σ ~ InverseGamma(1,1)

    for i in eachindex(x)
        y[i] ~ Normal(intercept + slope * x[i], σ)
    end
end

@model function linear_regression_2(x, y)
    slope ~ Normal(0, 10)
    intercept ~ Normal(0, 10)
    σ ~ Normal(0, 1) # error

    for i in eachindex(x)
        y[i] ~ Normal(intercept + slope * x[i], σ)
    end
end


model = linear_regression_2(x, y)


chain = sample(linear_regression(x, y), NUTS(0.65), 3_000)
display(mean(chain))


RUN_ERRONEOUS_CODE = false
if RUN_ERRONEOUS_CODE
    chain = sample(linear_regression_2(x, y), NUTS(0.65), 3_000) # will error
end
