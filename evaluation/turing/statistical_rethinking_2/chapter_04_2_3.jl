# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_04_part_2.jl

using Turing


@model function height_regr_model_N(weight, height)
    a ~ Normal(178, 20)
    b ~ LogNormal(0, 1)
    m_weight = mean(weight)
    μ = @. a + b * (weight - m_weight)
    σ ~ Uniform(0, 50)
    height ~ MvNormal(μ, σ)
end

model = height_regr_model_N

# MODELGRAPH:
# nodes:
# a, b, σ, height
# edges:
# a -> height
# b -> height
# σ -> height
# END_MODELGRAPH