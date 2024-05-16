# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_04_part_3.jl

using Turing

@model function model_splines_matrix(doy)
    w ~ MvNormal(zeros(length(basis)), 1)
    a ~ Normal(100, 10)
    μ = a .+ B * w
    σ ~ Exponential(1)
    doy ~ MvNormal(μ, σ)
end

model = model_splines_matrix

# MODELGRAPH:
# nodes:
# w, a, σ, doy
# edges:
# w -> doy
# a -> doy
# σ -> doy
# END_MODELGRAPH