# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_05_1_Spurious_Associations.jl

using Turing

@model function m5_3(A, M, D)
    σ ~ Exponential(1)
    a ~ Normal(0, 0.2)
    bA ~ Normal(0, 0.5)
    bM ~ Normal(0, 0.5)
    μ = @. a + bA * A + bM * M
    D ~ MvNormal(μ, σ)
end

model = m5_3

# MODELGRAPH:
# nodes:
# σ, a, bA, bM, D
# edges:
# σ -> D
# a -> D
# bA -> D
# bM -> D
# END_MODELGRAPH