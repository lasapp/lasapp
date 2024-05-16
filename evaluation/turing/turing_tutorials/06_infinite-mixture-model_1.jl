# https://github.com/TuringLang/TuringTutorials/tree/8515a567321adf1531974dd14eb29c00eea05648

using Turing

@model function two_model(x)
    # Hyper-parameters
    μ0 = 0.0
    σ0 = 1.0

    # Draw weights.
    π1 ~ Beta(1, 1)
    π2 = 1 - π1

    # Draw locations of the components.
    μ1 ~ Normal(μ0, σ0)
    μ2 ~ Normal(μ0, σ0)

    # Draw latent assignment.
    z ~ Categorical([π1, π2])

    # Draw observation from selected component.
    if z == 1
        x ~ Normal(μ1, 1.0)
    else
        x ~ Normal(μ2, 1.0)
    end
end

model = two_model

# MODELGRAPH:
# nodes:
# π1, μ1, μ2, z, x
# edges:
# π1 -> z
# z -> x
# μ1 -> x
# μ2 -> x
# END_MODELGRAPH