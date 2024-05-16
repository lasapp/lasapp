# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_04_part_1.jl

using Turing

@model function m4_2(height)
    μ ~ Normal(178, 0.1)
    σ ~ Uniform(0, 50)
    height ~ Normal(μ, σ)
end

model = m4_2

# MODELGRAPH:
# nodes:
# μ, σ, height
# edges:
# μ -> height
# σ -> height
# END_MODELGRAPH