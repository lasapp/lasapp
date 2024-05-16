# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_04_part_3.jl

using Turing

@model function model_splines(year, doy)
    w ~ MvNormal(zeros(length(basis)), 1)
    a ~ Normal(100, 10)
    s = Spline(basis, w)
    μ = a .+ s.(year)
    σ ~ Exponential(1)
    doy ~ MvNormal(μ, σ)
end

model = model_splines

# MODELGRAPH:
# nodes:
# w, a, σ, doy
# edges:
# w -> doy
# a -> doy
# σ -> doy
# END_MODELGRAPH

# function depends on RV works because it is not a user-defined function