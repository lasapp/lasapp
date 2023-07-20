using Gen
import Random
Random.seed!(0)

x = randn(25)
y = 2 .* x .- 1 .+ randn(length(x))

@gen function linear_regression(x)
    slope = {:slope} ~ normal(0, sqrt(3))
    intercept ~ normal(0, sqrt(3))
    σ ~ inv_gamma(2,3)
    for i in eachindex(x)
        {:y=>i} ~ normal(intercept + slope * x[i], σ)
    end
end
@gen function linear_regression_2(x)
    slope = {:slope} ~ normal(0, sqrt(3))
    intercept ~ normal(0, sqrt(3))
    σ ~ normal(0,1)
    for i in eachindex(x)
        {:y=>i} ~ normal(intercept + slope * x[i], σ)
    end
end
model = linear_regression_2

observations = choicemap()
for i in eachindex(x)
    observations[:y=>i] = y[i]
end

function do_inference(model)
    trace, = generate(model, (x,), observations)
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

    println("slope: ", sum(slopes) / length(slopes))
    println("intercepts: ", sum(intercepts) / length(intercepts))
    println("sigma: ", sum(σs) / length(σs))
end

do_inference(linear_regression)

RUN_ERRONEOUS_CODE = false
if RUN_ERRONEOUS_CODE
    do_inference(linear_regression_2) # will error
end

using LinearAlgebra: I
@gen (static) function static_linear_regression(x)
    slope = {:slope} ~ normal(0, sqrt(3))
    intercept ~ normal(0, sqrt(3))
    σ ~ inv_gamma(2,3)
    {:y} ~ mvnormal(intercept .+ slope .* x, σ*I(length(x)))
end
using PyCall
@pyimport graphviz
using Gen: draw_graph
draw_graph(static_linear_regression, graphviz, "tmp/graph")
