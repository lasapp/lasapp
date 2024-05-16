# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_13.jl

using Turing

@model function m13_7(N)
    v ~ Normal(0, 3)
    x ~ Normal(0, exp(v))
end

model = m13_7

# MODELGRAPH:
# nodes:
# v, x
# edges:
# v -> x
# END_MODELGRAPH
