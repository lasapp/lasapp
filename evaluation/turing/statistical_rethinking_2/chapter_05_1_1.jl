# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_05_1_Spurious_Associations.jl

using Turing

@model function m5_1(A, D)
    σ ~ Exponential(1)
    a ~ Normal(0, 0.2)
    bA ~ Normal(0, 0.5)
    μ = @. a + bA * A
    D ~ MvNormal(μ, σ)
end

model = m5_1

# MODELGRAPH:
# nodes:
# σ, a, bA, D
# edges:
# σ -> D
# a -> D
# bA -> D
# END_MODELGRAPH