# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_13.jl

using Turing

@model function m13_1(S, N, tank)
    tank_size = length(levels(tank))
    a ~ filldist(Normal(0, 1.5), tank_size)
    p = logistic.(a)
    @. S ~ Binomial(N, p)
end

model = m13_1

# MODELGRAPH:
# nodes:
# a, S
# edges:
# a -> S
# END_MODELGRAPH

# NOTE: constraint violation due to function input