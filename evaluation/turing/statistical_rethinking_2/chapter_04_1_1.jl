# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_04_part_1.jl

using Turing

@model function model_height1(height)
    μ ~ Normal(178, 20)
    σ ~ Uniform(0, 50)
    height ~ Normal(μ, σ)
end

model = model_height1

# MODELGRAPH:
# nodes:
# μ, σ, height
# edges:
# μ -> height
# σ -> height
# END_MODELGRAPH