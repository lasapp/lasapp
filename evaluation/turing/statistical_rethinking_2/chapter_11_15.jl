# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_11.jl

using Turing

@model function m11_14(career, family_income)
    a ~ MvNormal([0, 0], 1.5)
    b ~ MvNormal([0, 0], 1)
    
    for i ∈ eachindex(career)
        income = family_income[i]
        s = [a[1] + b[1] * income, a[2] + b[2] * income, 0]
        p = softmax(s)
        career[i] ~ Categorical(p)
    end
end

model = m11_14

# MODELGRAPH:
# nodes:
# a, b, career[i]
# edges:
# a -> career[i]
# b -> career[i]
# END_MODELGRAPH

# NOTE: unroll loops to remove spurious edge career[i] -> career[i]

# NOTE: constraint violation due to softmax - simplex (multivariate)