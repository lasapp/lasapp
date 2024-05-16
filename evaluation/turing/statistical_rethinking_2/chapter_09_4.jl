# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_09.jl

using Turing

@model function model_m9_3(y)
    α ~ Normal(1, 10)
    σ ~ Exponential(1)
    y ~ Normal(α, σ)
end

model = model_m9_3

# MODELGRAPH:
# nodes:
# α, σ, y
# edges:
# α -> y
# σ -> y
# END_MODELGRAPH