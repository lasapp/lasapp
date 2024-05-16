# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_13.jl

using Turing

@model function m13_3(Si, Ni, pond)
    σ ~ Exponential()
    ā ~ Normal(0, 1.5)
    a_pond ~ filldist(Normal(ā, σ), nponds)
    p = logistic.(a_pond)
    @. Si ~ Binomial(Ni, p)
end

model = m13_3

# MODELGRAPH:
# nodes:
# σ, ā, a_pond, Si
# edges:
# ā -> a_pond
# σ -> a_pond
# a_pond -> Si
# END_MODELGRAPH

# NOTE: constraint violation due to function input