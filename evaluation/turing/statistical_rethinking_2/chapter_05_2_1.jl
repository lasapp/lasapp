# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_05_2_Masked_Relationships.jl

using Turing

@model function model_m5_5_draft(N, K)
    a ~ Normal(0, 1)
    bN ~ Normal(0, 1)
    σ ~ Exponential(1)
    μ = @. a + bN * N
    K ~ MvNormal(μ, σ)
end

model = model_m5_5_draft

# MODELGRAPH:
# nodes:
# a, bN, σ, K
# edges:
# a -> K
# bN -> K
# σ -> K
# END_MODELGRAPH