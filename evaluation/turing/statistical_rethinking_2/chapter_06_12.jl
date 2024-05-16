# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_06.jl

using Turing

@model function model_m6_12(P, G, U, C)
    a ~ Normal()
    b_PC ~ Normal()
    b_GC ~ Normal()
    b_U ~ Normal()
    μ = @. a + b_PC*P + b_GC*G + b_U*U
    σ ~ Exponential(1)
    C ~ MvNormal(μ, σ)
end

model = model_m6_12

# MODELGRAPH:
# nodes:
# a, b_PC, b_GC, σ, b_U, C
# edges:
# a -> C
# b_PC -> C
# b_U -> C
# b_GC -> C
# σ -> C
# END_MODELGRAPH