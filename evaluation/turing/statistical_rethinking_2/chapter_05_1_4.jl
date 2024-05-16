# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_05_1_Spurious_Associations.jl

using Turing

@model function m5_4(A, M)
    σ ~ Exponential(1)
    a ~ Normal(0, 0.2)
    bAM ~ Normal(0, 0.5)
    μ = @. a + bAM * A
    M ~ MvNormal(μ, σ)
end

model = m5_4

# MODELGRAPH:
# nodes:
# σ, a, bAM, M
# edges:
# σ -> M
# a -> M
# bAM -> M
# END_MODELGRAPH