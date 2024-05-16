# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_04_part_2.jl

using Turing


@model function height_regr_model_exp1(weight, height)
    a ~ Normal(178, 20)
    log_b ~ Normal(0, 1)
    μ = @. a + exp(log_b) * (weight - xbar)
    σ ~ Uniform(0, 50)
    height ~ MvNormal(μ, σ)
end

model = height_regr_model_exp1

# MODELGRAPH:
# nodes:
# a, log_b, σ, height
# edges:
# a -> height
# log_b -> height
# σ -> height
# END_MODELGRAPH