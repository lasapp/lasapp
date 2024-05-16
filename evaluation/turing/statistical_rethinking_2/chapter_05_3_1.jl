# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_05_3_Categorical_Variables.jl

using Turing

@model function model_m5_8(sex, height)
    σ ~ Uniform(0, 50)
    a ~ MvNormal([178, 178], 20)
    height ~ MvNormal(a[sex], σ)
end

model = model_m5_8

# MODELGRAPH:
# nodes:
# σ, a, height
# edges:
# a -> height
# σ -> height
# END_MODELGRAPH

# NOTE: interval arithmetic: vect