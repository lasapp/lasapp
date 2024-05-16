# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_12.jl

using Turing

@model function m12_7(R, action, intention, contact, edu_norm)
    bA ~ Normal()
    bI ~ Normal()
    bC ~ Normal()
    bE ~ Normal()

    phi = @. bE*edu_norm + bA*action + bI*intention + bC*contact

    # use same cutpoints as before
    Δ_cutpoints ~ filldist(Exponential(), 6)
    cutpoints = -3 .+ cumsum(Δ_cutpoints)
    
    for i ∈ eachindex(R)
        R[i] ~ OrderedLogistic(phi[i], cutpoints)
    end
end

model = m12_7

# MODELGRAPH:
# nodes:
# bA, bI, bC, bE, Δ_cutpoints, R[i]
# edges:
# Δ_cutpoints -> R[i]
# bA -> R[i]
# bI -> R[i]
# bC -> R[i]
# bE -> R[i]
# END_MODELGRAPH

# NOTE: unroll loops to remove spurious edge R[i] -> R[i]
# NOTE: Constraint violation due to unknown OrderedLogistic