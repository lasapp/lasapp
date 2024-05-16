# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_09.jl

using Turing

@model function model_m8_3(rugged_std, cid,  log_gdp_std)
    σ ~ Exponential()
    a ~ MvNormal([1, 1], 0.1)
    b ~ MvNormal([0, 0], 0.3)
    μ = @. a[cid] + b[cid] * (rugged_std - r̄)
    log_gdp_std ~ MvNormal(μ, σ)
end

model = model_m8_3

# MODELGRAPH:
# nodes:
# σ, a, b, log_gdp_std
# edges:
# a -> log_gdp_std
# b -> log_gdp_std
# σ -> log_gdp_std
# END_MODELGRAPH