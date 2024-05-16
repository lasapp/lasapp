# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_13.jl

using Turing

@model function m13_2(S, N, tank)
    tank_size = length(levels(tank))
    σ ~ Exponential()
    ā ~ Normal(0, 1.5)
    a ~ filldist(Normal(ā, σ), tank_size)
    p = logistic.(a)
    @. S ~ Binomial(N, p)
end

model = m13_2

# MODELGRAPH:
# nodes:
# σ, ā, a, S
# edges:
# ā -> a
# σ -> a
# a -> S
# END_MODELGRAPH

# NOTE: constraint violation due to function input