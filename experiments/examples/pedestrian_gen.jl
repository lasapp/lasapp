using Gen
import Random
Random.seed!(0)

@gen function pedestrian()
    start ~ uniform_continuous(0,3)
    t = 0
    position = start
    distance = 0.0
    while position > 0 && distance < 10
        step = {:step=>t} ~ uniform_continuous(-1, 1)
        distance = distance + abs(step)
        position = position + step
        t = t + 1
    end
    end_distance ~ normal(distance, 0.1)
    return start
end
model = pedestrian
observations = choicemap(:end_distance=>1.1)

traces, log_norm_weights, lml_est = importance_sampling(model, (), observations, 5000)

starts = []
for i in eachindex(traces)
    tr = traces[i]
    push!(starts, tr[:start])
end
weights = exp.(log_norm_weights)

starts_mean = starts'weights
println("starts_mean=$starts_mean")