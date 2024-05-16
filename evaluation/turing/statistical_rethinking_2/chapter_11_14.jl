# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_11.jl

using Turing

@model function m11_13(career, income)
    a ~ MvNormal([0, 0], 1)
    b ~ TruncatedNormal(0, 0.5, 0, Inf)
    p = softmax([a[1] + b*income[1], a[2] + b*income[2], 0])
    career ~ Categorical(p)
end

model = m11_13

# MODELGRAPH:
# nodes:
# a, b, career
# edges:
# a -> career
# b -> career
# END_MODELGRAPH

# NOTE: constraint violation due to softmax - simplex (multivariate)