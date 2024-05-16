# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_06.jl

using Turing

@model function model_m6_1(leg_left, leg_right, height)
    a ~ Normal(10, 100)
    bl ~ Normal(2, 10)
    br ~ Normal(2, 10)
    μ = @. a + bl * leg_left + br * leg_right
    σ ~ Exponential(1)
    height ~ MvNormal(μ, σ)
end

model = model_m6_1

# MODELGRAPH:
# nodes:
# a, bl, br, σ, height
# edges:
# a -> height
# bl -> height
# br -> height
# σ -> height
# END_MODELGRAPH