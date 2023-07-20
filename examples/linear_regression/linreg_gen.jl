
using Gen
import Random
using LinearAlgebra: I

Random.seed!(0)
x = randn(25)
y = 2 .* x .- 1 .+ randn(length(x))

@gen function linear_regression(x)
    # Set slope prior.
    slope = {:slope} ~ normal(0, sqrt(3))

    # Set intercept prior.
    intercept ~ normal(0, sqrt(3))

    # Set variance prior.
    σ ~ inv_gamma(2,3)

    y ~ mvnormal(intercept .+ slope * x, σ*I(length(x)))
    # {:y} ~ mvnormal(intercept .+ slope * x, σ*I(length(x)))
end
model = linear_regression

observations = choicemap(:y => y)
observations[:slope] = 2.
observations[:intercept] = 1.

function do_inference()
    trace, = generate(linear_regression, (x,), observations)
    slopes = Float64[]
    intercepts = Float64[]
    σs = Float64[]
    for i=1:1000
        trace, = mh(trace, select(:slope))
        trace, = mh(trace, select(:intercept))
        trace, = mh(trace, select(:σ))
        push!(slopes, trace[:slope])
        push!(intercepts, trace[:intercept])
        push!(σs, trace[:σ])
    end

    println(sum(slopes) / length(slopes))
    println(sum(intercepts) / length(intercepts))
    println(sum(σs) / length(σs))
end

do_inference()