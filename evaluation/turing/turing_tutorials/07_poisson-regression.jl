# https://github.com/TuringLang/TuringTutorials/tree/8515a567321adf1531974dd14eb29c00eea05648

using Turing

@model function poisson_regression(x, y, n, σ²)
    b0 ~ Normal(0, σ²)
    b1 ~ Normal(0, σ²)
    b2 ~ Normal(0, σ²)
    b3 ~ Normal(0, σ²)
    for i in 1:n
        theta = b0 + b1 * x[i, 1] + b2 * x[i, 2] + b3 * x[i, 3]
        y[i] ~ Poisson(exp(theta))
    end
end

model = poisson_regression

# MODELGRAPH:
# nodes:
# b0, b1, b2, b3, y[i]
# edges:
# b0 -> y[i]
# b1 -> y[i]
# b2 -> y[i]
# b3 -> y[i]
# END_MODELGRAPH

# NOTE: constraint violation due to function input