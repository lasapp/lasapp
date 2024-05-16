# https://github.com/TuringLang/TuringTutorials/tree/8515a567321adf1531974dd14eb29c00eea05648

using Turing

@model function logistic_regression(x, y, σ)
    n = size(x, 1)
    length(y) == n ||
        throw(DimensionMismatch("number of observations in `x` and `y` is not equal"))

    # Priors of intercepts and coefficients.
    intercept_versicolor ~ Normal(0, σ)
    intercept_virginica ~ Normal(0, σ)
    coefficients_versicolor ~ MvNormal(Zeros(4), σ^2 * I)
    coefficients_virginica ~ MvNormal(Zeros(4), σ^2 * I)

    # Compute the likelihood of the observations.
    values_versicolor = intercept_versicolor .+ x * coefficients_versicolor
    values_virginica = intercept_virginica .+ x * coefficients_virginica
    for i in 1:n
        # the 0 corresponds to the base category `setosa`
        v = softmax([0, values_versicolor[i], values_virginica[i]])
        y[i] ~ Categorical(v)
    end
end

model = logistic_regression

# MODELGRAPH:
# nodes:
# intercept_versicolor, intercept_virginica, coefficients_versicolor, coefficients_virginica, y[i]
# edges:
# intercept_versicolor -> y[i]
# intercept_virginica -> y[i]
# coefficients_versicolor -> y[i]
# coefficients_virginica -> y[i]
# END_MODELGRAPH