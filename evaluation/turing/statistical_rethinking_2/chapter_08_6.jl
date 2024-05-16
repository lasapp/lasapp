# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_08.jl

using Turing

@model function m8_5(water_cent, shade_cent, blooms_std)
    a ~ Normal(0.5, 0.25)
    bw ~ Normal(0, 0.25)
    bs ~ Normal(0, 0.25)
    bws ~ Normal(0, 0.25)
    μ = @. a + bw*water_cent + bs*shade_cent + bws*water_cent*shade_cent
    σ ~ Exponential(1)
    blooms_std ~ MvNormal(μ, σ)
end

model = m8_5

# MODELGRAPH:
# nodes:
# a, bw, bs, bws, σ, blooms_std
# edges:
# a -> blooms_std
# bw -> blooms_std
# bs -> blooms_std
# bws -> blooms_std
# σ -> blooms_std
# END_MODELGRAPH