# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_13.jl

using Turing

@model function m13_5(pulled_left, actor, treatment)
    σ_a ~ Exponential()
    ā ~ Normal(0, 1.5)
    actors_count = length(levels(actor))
    treats_count = length(levels(treatment))
    a ~ filldist(Normal(ā, σ_a), actors_count)
    b ~ filldist(Normal(0, 0.5), treats_count)
    
    p = @. logistic(a[actor] + b[treatment])
    @. pulled_left ~ Binomial(1, p)
end


model = m13_5

# MODELGRAPH:
# nodes:
# σ_a, ā, a, b, pulled_left
# edges:
# ā -> a
# σ_a -> a
# a -> pulled_left
# b -> pulled_left
# END_MODELGRAPH