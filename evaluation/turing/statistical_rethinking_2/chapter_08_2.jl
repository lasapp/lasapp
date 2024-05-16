# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_08.jl

using Turing

@model function model_m8_1a(rugged_std, log_gdp_std)
    σ ~ Exponential()
    a ~ Normal(1, 0.1)
    b ~ Normal(0, 0.3)
    μ = @. a + b * (rugged_std - r̄_std)
    log_gdp_std ~ MvNormal(μ, σ)
end

model = model_m8_1a

# MODELGRAPH:
# nodes:
# σ, a, b, log_gdp_std
# edges:
# a -> log_gdp_std
# b -> log_gdp_std
# σ -> log_gdp_std
# END_MODELGRAPH