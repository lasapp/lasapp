# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_11.jl

using Turing

@model function m11_10(T, cid, P)
    a ~ MvNormal([3, 3], 0.5)
    b ~ MvNormal([0, 0], 0.2)
    λ = @. exp(a[cid] + b[cid]*P)
    for i ∈ eachindex(T)
        T[i] ~ Poisson(λ[i])
    end
end

model = m11_10

# MODELGRAPH:
# nodes:
# a, b, T[i]
# edges:
# a -> T[i]
# b -> T[i]
# END_MODELGRAPH

# NOTE: unroll loops to remove spurious edge T[i] -> T[i]