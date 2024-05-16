# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_12.jl

using Turing

@model function m12_2(T, P, cid)
    g ~ Exponential()
    ϕ ~ Exponential()
    a ~ MvNormal([1,1], 1)
    b₁ ~ Exponential()
    b₂ ~ Exponential()
    b = [b₁, b₂]
    λ = @. exp(a[cid])*(P^b[cid]) / g
    p = 1/(ϕ+1)
    r = λ/ϕ
    clamp!(r, 0.01, Inf)
    p = clamp(p, 0.01, 1)
    @. T ~ NegativeBinomial(r, p)
end

model = m12_2

# MODELGRAPH:
# nodes:
# g, ϕ, a, b₁, b₂, T
# edges:
# g -> T
# ϕ -> T
# a -> T
# b₁ -> T
# b₂ -> T
# END_MODELGRAPH