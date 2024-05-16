# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_11.jl

using Turing

@model function model_m11_8(admit, applications, gid, dept_id)
    a ~ MvNormal([0, 0], 1.5)
    delta ~ MvNormal(zeros(6), 1.5)
    p = @. logistic(a[gid] + delta[dept_id])
    for i ∈ eachindex(applications)
        admit[i] ~ Binomial(applications[i], p[i])
    end
end

model = model_m11_8

# MODELGRAPH:
# nodes:
# a, delta, admit[i]
# edges:
# a -> admit[i]
# delta -> admit[i]
# END_MODELGRAPH

# NOTE: constraint violation due to function input