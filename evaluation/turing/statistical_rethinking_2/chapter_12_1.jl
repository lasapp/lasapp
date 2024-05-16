# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_12.jl

using Turing

@model function m12_1(A, N, gid)
    a ~ MvNormal([0, 0], 1.5)
    p̄ = @. logistic(a[gid])
    ϕ ~ Exponential(1)
    θ = ϕ + 2
    @. A ~ BetaBinomial2(N, p̄, θ)
end


model = m12_1

# MODELGRAPH:
# nodes:
# a, ϕ, A
# edges:
# a -> A
# ϕ -> A
# END_MODELGRAPH

# NOTE: constraint violation due to unknown BetaBinomial2