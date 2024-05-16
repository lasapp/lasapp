# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_04_part_1.jl

using Turing

@model function m4_3(x, y)
    s ~ InverseGamma(2, 3)
    m ~ Normal(0, sqrt(s))
    x ~ Normal(m, sqrt(s))
    y ~ Normal(m, sqrt(s))
end

model = m4_3

# MODELGRAPH:
# nodes:
# s, m, x, y
# edges:
# s -> m
# s -> x
# s -> y
# m -> x
# m -> y
# END_MODELGRAPH