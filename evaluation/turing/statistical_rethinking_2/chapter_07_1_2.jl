# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_07.jl

using Turing

@model function model_m7_2(mass_std, brain_std)
    a ~ Normal(0.5, 1)
    b ~ MvNormal([0, 0], 10)
    μ = @. a + b[1]*mass_std + b[2]*mass_std^2
    log_σ ~ Normal()
    brain_std ~ MvNormal(μ, exp(log_σ))
end

model = model_m7_2

# MODELGRAPH:
# nodes:
# a, b, log_σ, brain_std
# edges:
# a -> brain_std
# b -> brain_std
# log_σ -> brain_std
# END_MODELGRAPH

# NOTE: interval arithmetic vect