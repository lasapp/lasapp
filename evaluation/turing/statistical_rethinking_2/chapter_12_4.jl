# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_12.jl

using Turing

@model function m12_4(R)
    # to ensure sorted cutpoints, use deltas
    Δ_cutpoints ~ filldist(Exponential(), 6)
    cutpoints = -2 .+ cumsum(Δ_cutpoints)
    R .~ OrderedLogistic(0, cutpoints)
end

model = m12_4

# MODELGRAPH:
# nodes:
# Δ_cutpoints, R
# edges:
# Δ_cutpoints -> R
# END_MODELGRAPH

# NOTE: OrderedLogistic
# NOTE: Constraint violation due to unknown OrderedLogistic