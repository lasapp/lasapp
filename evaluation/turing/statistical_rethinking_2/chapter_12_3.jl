# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_12.jl

using Turing

@model function m12_3(y)
    ap ~ Normal(-1.5, 1)
    al ~ Normal(1, 0.5)
    λ = exp(al)
    p = logistic(ap)
    y .~ ZIPoisson(λ, p)
end

model = m12_3

# MODELGRAPH:
# nodes:
# ap, al, y
# edges:
# ap -> y
# al -> y
# END_MODELGRAPH

# NOTE: Constraint violation due to unknown ZIPoisson