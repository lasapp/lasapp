# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_11.jl

using Turing

@model function m_pois(admit, reject)
    a ~ MvNormal([0, 0], 1.5)
    λ = exp.(a)
    admit ~ Poisson(λ[1])
    reject ~ Poisson(λ[2])
end

model = m_pois

# MODELGRAPH:
# nodes:
# a, admit, reject
# edges:
# a -> admit
# a -> reject
# END_MODELGRAPH
