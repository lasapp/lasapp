# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_02.jl

using Turing

@model function m2_0(W, L)
    p ~ Uniform(0, 1)
    W ~ Binomial(W + L, p)
end

model = m2_0

# MODELGRAPH:
# nodes:
# p, W
# edges:
# p -> W
# END_MODELGRAPH

# NOTE: constraint violation warning, because of function inputs W, L