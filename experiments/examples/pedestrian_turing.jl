using Turing
import Random
Random.seed!(0)

@model function pedestrian(end_distance)
    start ~ Uniform(0,3)
    t = 0
    position = start
    distance = 0.0
    step = Dict()
    while position > 0 && position < 10
        t = t + 1
        step[t] ~ Uniform(-1, 1)
        distance = distance + abs(step[t])
        position = position + step[t]
    end
    end_distance ~ Normal(distance, 0.1)
    return start
end
model = pedestrian(1.1)


res = sample(model, IS(), 10000);

weights = exp.(res[:lp]) / sum(exp, res[:lp])
starts_mean = ((res[:start])'weights)
starts_mean = starts_mean[1]
println("starts_mean=$starts_mean")


RUN_ERRONEOUS_CODE = false
if RUN_ERRONEOUS_CODE
    sample(model, HMC(0.1, 10), 3000) # ERROR: LoadError: KeyError: key step[26] not found
end
