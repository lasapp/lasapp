# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_12.jl

using Turing

@model function m12_5(R, A, I, C)
    # to ensure sorted cutpoints, use deltas
    Δ_cutpoints ~ filldist(Exponential(), 6)
    cutpoints = -3 .+ cumsum(Δ_cutpoints)
    
    bA ~ Normal(0, 0.5)
    bI ~ Normal(0, 0.5)
    bC ~ Normal(0, 0.5)
    bIA ~ Normal(0, 0.5)
    bIC ~ Normal(0, 0.5)
    BI = @. bI + bIA*A + bIC*C
    phi = @. bA*A + bC*C + BI*I
    
    for i in eachindex(R)
        R[i] ~ OrderedLogistic(phi[i], cutpoints)
    end
end

model = m12_5

# MODELGRAPH:
# nodes:
# Δ_cutpoints, bA, bI, bC, bIA, bIC, R[i]
# edges:
# Δ_cutpoints -> R[i]
# bA -> R[i]
# bI -> R[i]
# bC -> R[i]
# bIA -> R[i]
# bIC -> R[i]
# END_MODELGRAPH

# NOTE: unroll loops to remove spurious edge R[i] -> R[i]
# NOTE: Constraint violation due to unknown OrderedLogistic