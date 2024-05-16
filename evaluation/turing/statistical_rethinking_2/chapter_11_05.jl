# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_11.jl

using Turing

@model function m11_5(actor, side, cond, pulled_left)
    act_levels = length(levels(actor))
    a ~ MvNormal(zeros(act_levels), 1.5)
    side_levels = length(levels(side))
    bs ~ MvNormal(zeros(side_levels), 0.5)    
    cond_levels = length(levels(cond))
    bc ~ MvNormal(zeros(cond_levels), 0.5)
    
    p = @. logistic(a[actor] + bs[side] + bc[cond])
    for i ∈ eachindex(pulled_left)
        pulled_left[i] ~ Binomial(1, p[i])
    end
end

model = m11_5

# MODELGRAPH:
# nodes:
# a, bs, bc, pulled_left[i]
# edges:
# a -> pulled_left[i]
# bs -> pulled_left[i]
# bc -> pulled_left[i]
# END_MODELGRAPH

# NOTE: unroll loops to remove spurious edge pulled_left[i] -> pulled_left[i]