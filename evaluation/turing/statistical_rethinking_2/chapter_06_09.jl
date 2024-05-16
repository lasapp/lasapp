# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_06.jl

using Turing

@model function model_m6_9(mid, A, happiness)
    a ~ MvNormal([0, 0], 1)
    bA ~ Normal(0, 2)
    μ = a[mid] .+ bA .* A
    σ ~ Exponential(1)
    happiness ~ MvNormal(μ, σ)
end

model = model_m6_9

# MODELGRAPH:
# nodes:
# a, bA, σ, happiness
# edges:
# a -> happiness
# bA -> happiness
# σ -> happiness
# END_MODELGRAPH

# NOTE: interval arithmetic vect