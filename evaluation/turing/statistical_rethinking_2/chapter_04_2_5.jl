# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_04_part_2.jl

using Turing


@model function height_regr_m3(weight_s, weight_s2, weight_s3, height)
    a ~ Normal(178, 20)
    b1 ~ LogNormal(0, 1)
    b2 ~ Normal(0, 1)
    b3 ~ Normal(0, 1)
    μ = @. a + b1 * weight_s + b2 * weight_s2 + b3 * weight_s3
    σ ~ Uniform(0, 50)
    height ~ MvNormal(μ, σ)
end

model = height_regr_m3

# MODELGRAPH:
# nodes:
# a, b1, b2, b3, σ, height
# edges:
# a -> height
# b1 -> height
# b2 -> height
# b3 -> height
# σ -> height
# END_MODELGRAPH