# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_05_3_Categorical_Variables.jl

using Turing

@model function model_m5_9(clade_id, K)
    clade_μ = zeros(clade_counts)
    a ~ MvNormal(clade_μ, 0.5)
    σ ~ Exponential(1)
    K ~ MvNormal(a[clade_id], σ)
end

model = model_m5_9

# MODELGRAPH:
# nodes:
# σ, a, K
# edges:
# a -> K
# σ -> K
# END_MODELGRAPH