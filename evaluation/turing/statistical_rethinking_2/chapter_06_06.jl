# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_06.jl

using Turing

@model function model_m6_6(h0, h1)
    p ~ LogNormal(0, 0.25)
    σ ~ Exponential(1)
    μ = h0 .* p
    h1 ~ MvNormal(μ, σ)
end

model = model_m6_6

# MODELGRAPH:
# nodes:
# p, σ, h1
# edges:
# p -> h1
# σ -> h1
# END_MODELGRAPH