# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_13.jl

using Turing

@model function m13_6(pulled_left, actor, block_id, treatment)
    σ_a ~ Exponential()
    σ_g ~ Exponential()
    σ_b ~ Exponential()
    ā ~ Normal(0, 1.5)
    actors_count = length(levels(actor))
    blocks_count = length(levels(block_id))
    treats_count = length(levels(treatment))
    a ~ filldist(Normal(ā, σ_a), actors_count)
    g ~ filldist(Normal(0, σ_g), blocks_count)
    b ~ filldist(Normal(0, σ_b), treats_count)
    
    p = @. logistic(a[actor] + g[block_id] + b[treatment])
    @. pulled_left ~ Binomial(1, p)
end

model = m13_6

# MODELGRAPH:
# nodes:
# ā, σ_a, σ_g, σ_b, a, g, b, pulled_left
# edges:
# ā -> a
# σ_a -> a
# σ_g -> g
# σ_b -> b
# a -> pulled_left
# b -> pulled_left
# g -> pulled_left
# END_MODELGRAPH