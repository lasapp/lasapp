# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_12.jl

using Turing

@model function m12_6(R, action, intention, contact, E)
    delta ~ Dirichlet(7, 2)
    pushfirst!(delta, 0.0)
    
    bA ~ Normal()
    bI ~ Normal()
    bC ~ Normal()
    bE ~ Normal()

    # sum all education's deltas
    sE = sum.(map(i -> delta[1:i], E))
    phi = @. bE*sE + bA*action + bI*intention + bC*contact

    # use same cutpoints as before
    Δ_cutpoints ~ filldist(Exponential(), 6)
    cutpoints = -3 .+ cumsum(Δ_cutpoints)
    
    for i ∈ eachindex(R)
        R[i] ~ OrderedLogistic(phi[i], cutpoints)
    end
end

model = m12_6

# MODELGRAPH:
# nodes:
# delta, bA, bI, bC, bE, Δ_cutpoints, R[i]
# edges:
# Δ_cutpoints -> R[i]
# bA -> R[i]
# bI -> R[i]
# bC -> R[i]
# bE -> R[i]
# delta -> R[i]
# END_MODELGRAPH

# NOTE: unroll loops to remove spurious edge R[i] -> R[i]
# NOTE: fails to build syntax tree due to lambda