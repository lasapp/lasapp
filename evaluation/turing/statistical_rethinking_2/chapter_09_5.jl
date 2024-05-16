# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_09.jl

using Turing

@model function model_m9_4(y)
    a1 ~ Normal(0, 1000)
    a2 ~ Normal(0, 1000)
    σ ~ Exponential(1)
    μ = a1 + a2
    y ~ Normal(μ, σ)
end

model = model_m9_4

# MODELGRAPH:
# nodes:
# a1, a2, σ, y
# edges:
# a1 -> y
# a2 -> y
# σ -> y
# END_MODELGRAPH