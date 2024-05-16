# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_11.jl

using Turing

@model function m11_6(actor, treatment, left_pulls)
    act_levels = length(levels(actor))
    a ~ MvNormal(zeros(act_levels), 1.5)
    treat_levels = length(levels(treatment))
    b ~ MvNormal(zeros(treat_levels), 0.5)
    
    p = @. logistic(a[actor] + b[treatment])
    for i ∈ eachindex(left_pulls)
        left_pulls[i] ~ Binomial(18, p[i])
    end
end

model = m11_6

# MODELGRAPH:
# nodes:
# a, b, left_pulls[i]
# edges:
# a -> left_pulls[i]
# b -> left_pulls[i]
# END_MODELGRAPH

# NOTE: unroll loops to remove spurious edge left_pulls[i] -> left_pulls[i]