# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_11.jl

using Turing

@model function m11_4(actor, treatment, pulled_left)
    act_levels = length(levels(actor))
    a ~ MvNormal(zeros(act_levels), 1.5)
    treat_levels = length(levels(treatment))
    b ~ MvNormal(zeros(treat_levels), 0.5)
    
    p = @. logistic(a[actor] + b[treatment])
    for i ∈ eachindex(pulled_left)
        pulled_left[i] ~ Binomial(1, p[i])
    end
end

model = m11_4

# MODELGRAPH:
# nodes:
# a, b, pulled_left[i]
# edges:
# a -> pulled_left[i]
# b -> pulled_left[i]
# END_MODELGRAPH

# NOTE: unroll loops to remove spurious edge pulled_left[i] -> pulled_left[i]