# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_11.jl

using Turing

@model function m11_9(T)
    a ~ Normal(3, 0.5)
    λ = exp(a)
    T ~ Poisson(λ)
end

model = m11_9

# MODELGRAPH:
# nodes:
# a, T
# edges:
# a -> T
# END_MODELGRAPH