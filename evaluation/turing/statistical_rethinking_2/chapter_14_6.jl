# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_14.jl

using Turing

@model function m14_6(W, E, Q, WE)
    σ ~ filldist(Exponential(), 2)
    ρ ~ LKJ(2, 2)
    aW ~ Normal(0, 0.2)
    aE ~ Normal(0, 0.2) # BUG: identified redundant
    bEW ~ Normal(0, 0.5)
    bQE ~ Normal(0, 0.5)
    μW = @. aW + bEW*E
    μE = @. aW + bQE*Q # BUG: should be aE + bQE*Q
    Σ = (σ .* σ') .* ρ
    for i ∈ eachindex(WE)
        WE[i] ~ MvNormal([μW[i], μE[i]], Σ)
    end
end

model = m14_6

# MODELGRAPH:
# nodes:
# σ, ρ, aW, aE, bEW, bQE, WE[i]
# edges:
# σ -> WE[i]
# ρ -> WE[i]
# aW -> WE[i]
# bEW -> WE[i]
# bQE -> WE[i]
# END_MODELGRAPH

# NOTE: unroll loops to remove spurious edge WE[i] -> WE[i]
# NOTE: constraint violation due to multivariate covariance matrix
# NOTE: Bug found