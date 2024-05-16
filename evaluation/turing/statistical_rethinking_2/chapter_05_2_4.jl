# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_05_2_Masked_Relationships.jl

using Turing

@model function model_m5_7(N, M, K)
    a ~ Normal(0, 0.2)
    bN ~ Normal(0, 0.5)
    bM ~ Normal(0, 0.5)
    σ ~ Exponential(1)
    μ = @. a + bN * N + bM * M
    K ~ MvNormal(μ, σ)
end

model = model_m5_7

# MODELGRAPH:
# nodes:
# a, bN, bM, σ, K
# edges:
# a -> K
# bN -> K
# bM -> K
# σ -> K
# END_MODELGRAPH