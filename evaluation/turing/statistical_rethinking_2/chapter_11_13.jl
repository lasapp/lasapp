# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_11.jl

using Turing

@model function m11_12(y, log_days, monastery)
    a ~ Normal()
    b ~ Normal()
    λ = @. exp(log_days + a + b*monastery)
    @. y ~ Poisson(λ)
end


model = m11_12

# MODELGRAPH:
# nodes:
# a, b, y
# edges:
# a -> y
# b -> y
# END_MODELGRAPH