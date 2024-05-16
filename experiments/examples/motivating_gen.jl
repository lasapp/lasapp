using Gen
import Random
Random.seed!(0)

@gen function model()
    state ~ categorical([0.5, 0.5])
    if state-1 == 1
        mu = 5.
    else
        mu = 6.
    end
    for i in eachindex(X)
        {:x => i} ~ normal(mu, 1.)
    end
end

X = [4.81, 6.01, 4.62, 6.43, 5.85, 2.63, 6.20, 4.63, 6.02, 7.2]

observations = choicemap()
for i in eachindex(X)
    observations[:x => i] = X[i]
end

traces, log_norm_weights, lml_est = importance_sampling(model, (), observations, 5000)

states = []
for t in traces
    push!(states, t[:state] - 1)
end
weights = exp.(log_norm_weights)

state_mean = states'weights
println("state_mean=$state_mean")


function do_inference()
    trace, = generate(model, (), observations)
    states = Float64[]
    for i=1:1000
        trace, = hmc(trace, select(:state))
        push!(states, trace[:state])
    end
end

RUN_ERRONEOUS_CODE = false
if RUN_ERRONEOUS_CODE
    do_inference() # ERROR: LoadError: Gradient required but not available for return value of distribution Gen.Categorical()
end