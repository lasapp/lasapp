# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_11.jl

using Turing

@model function m11_7(admit, applications, gid)
    a ~ MvNormal([0, 0], 1.5)
    p = @. logistic(a[gid])
    for i ∈ eachindex(applications)
        admit[i] ~ Binomial(applications[i], p[i])
    end
end

model = m11_7

# MODELGRAPH:
# nodes:
# a, admit[i]
# edges:
# a -> admit[i]
# END_MODELGRAPH

# NOTE: constraint violation due to function input