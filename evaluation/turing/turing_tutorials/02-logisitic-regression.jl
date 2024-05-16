# https://github.com/TuringLang/TuringTutorials/tree/8515a567321adf1531974dd14eb29c00eea05648

using Turing

@model function logistic_regression(x, y, n, σ)
    intercept ~ Normal(0, σ)

    student ~ Normal(0, σ)
    balance ~ Normal(0, σ)
    income ~ Normal(0, σ)

    for i in 1:n
        v = logistic(intercept + student * x[i, 1] + balance * x[i, 2] + income * x[i, 3])
        y[i] ~ Bernoulli(v)
    end
end

model = logistic_regression

# MODELGRAPH:
# nodes:
# intercept, student, balance, income, y[i]
# edges:
# intercept -> y[i]
# student -> y[i]
# balance -> y[i]
# income -> y[i]
# END_MODELGRAPH

# NOTE: constraint violation due to function input