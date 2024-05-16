# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_11.jl

using Turing

@model function m11_11(T, P, cid)
    a ~ MvNormal([1,1], 1)
    b₁ ~ Exponential(1)
    b₂ ~ Exponential(1)
    b = [b₁, b₂]
    g ~ Exponential(1)
    λ = @. exp(a[cid]) * P ^ b[cid] / g
    for i ∈ eachindex(T)
        T[i] ~ Poisson(λ[i])
    end
end

model = m11_11

# MODELGRAPH:
# nodes:
# a, b₁, b₂, g, T[i]
# edges:
# a -> T[i]
# b₁ -> T[i]
# b₂ -> T[i]
# g -> T[i]
# END_MODELGRAPH

# NOTE: unroll loops to remove spurious edge T[i] -> T[i]