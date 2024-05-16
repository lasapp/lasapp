# https://github.com/TuringLang/TuringTutorials/tree/8515a567321adf1531974dd14eb29c00eea05648

using Turing

@model function decomp_model(t, c, op)
    α ~ Normal(0, 10)
    βt ~ Normal(0, 2)
    βc ~ MvNormal(Zeros(size(c, 2)), I)
    σ ~ truncated(Normal(0, 0.1); lower=0)

    cyclic = c * βc
    trend = α .+ βt .* t
    μ = op(trend, cyclic)
    y ~ MvNormal(μ, σ^2 * I)
    return (; trend, cyclic)
end

model = decomp_model

# MODELGRAPH:
# nodes:
# α, βt, βc, σ, y
# edges:
# α -> y
# σ -> y
# βt -> y
# βc -> y
# END_MODELGRAPH