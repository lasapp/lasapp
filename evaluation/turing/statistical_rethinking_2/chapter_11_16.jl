# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_11.jl

using Turing

@model function m_binom(admit, applications)
    a ~ Normal(0, 1.5)
    p = logistic(a)
    @. admit ~ Binomial(applications, p)
end

model = m_binom

# MODELGRAPH:
# nodes:
# a, admit
# edges:
# a -> admit
# END_MODELGRAPH

# NOTE: constraint violation due to function input