# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_14.jl

using Turing

@model function m14_4(W, E)
    σ ~ Exponential()
    aW ~ Normal(0, 0.2)
    bEW ~ Normal(0, 0.5)
    μ = @. aW + bEW * E
    W ~ MvNormal(μ, σ)
end

model = m14_4

# MODELGRAPH:
# nodes:
# σ, aW, bEW, W
# edges:
# σ -> W
# aW -> W
# bEW -> W
# END_MODELGRAPH
