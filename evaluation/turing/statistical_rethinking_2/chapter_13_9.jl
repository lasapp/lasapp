# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_13.jl

using Turing

@model function m13_4nc(pulled_left, actor, block_id, treatment)
    σ_a ~ Exponential()
    σ_g ~ Exponential()
    ā ~ Normal(0, 1.5)
    actors_count = length(levels(actor))
    blocks_count = length(levels(block_id))
    treats_count = length(levels(treatment))
    b ~ filldist(Normal(0, 0.5), treats_count)
    z ~ filldist(Normal(), actors_count)
    x ~ filldist(Normal(), blocks_count)
    a = @. ā + σ_a*z
    g = σ_g*x
    
    p = @. logistic(a[actor] + g[block_id] + b[treatment])
    @. pulled_left ~ Binomial(1, p)
end

model = m13_4nc

# MODELGRAPH:
# nodes:
# σ_a, σ_g, ā, b, z, x, pulled_left
# edges:
# σ_a -> pulled_left
# σ_g -> pulled_left
# ā -> pulled_left
# b -> pulled_left
# z -> pulled_left
# x -> pulled_left
# END_MODELGRAPH