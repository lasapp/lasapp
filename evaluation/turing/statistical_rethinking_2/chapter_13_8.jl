# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_13.jl

using Turing

@model function m13_7nc(N)
    v ~ Normal(0, 3)
    z ~ Normal()
    x = z * exp(v)
end

model = m13_7nc

# MODELGRAPH:
# nodes:
# v, z
# edges:
# END_MODELGRAPH
