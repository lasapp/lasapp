# https://github.com/TuringLang/TuringTutorials/tree/8515a567321adf1531974dd14eb29c00eea05648

using Turing

@model function infiniteGMM(x)
    # Hyper-parameters, i.e. concentration parameter and parameters of H.
    α = 1.0
    μ0 = 0.0
    σ0 = 1.0

    # Define random measure, e.g. Dirichlet process.
    rpm = DirichletProcess(α)

    # Define the base distribution, i.e. expected value of the Dirichlet process.
    H = Normal(μ0, σ0)

    # Latent assignment.
    z = tzeros(Int, length(x))

    # Locations of the infinitely many clusters.
    μ = tzeros(Float64, 0)

    for i in 1:length(x)

        # Number of clusters.
        K = maximum(z)
        nk = Vector{Int}(map(k -> sum(z .== k), 1:K))

        # Draw the latent assignment.
        z[i] ~ ChineseRestaurantProcess(rpm, nk)

        # Create a new cluster?
        if z[i] > K
            push!(μ, 0.0)

            # Draw location of new cluster.
            μ[z[i]] ~ H
        end

        # Draw observation.
        x[i] ~ Normal(μ[z[i]], 1.0)
    end
end

model = infiniteGMM

# MODELGRAPH:
# nodes:
# z[i], μ[z[i]], x[i]
# edges:
# z[i] -> μ[z[i]]
# μ[z[i]] -> x[i]
# END_MODELGRAPH

# NOTE: Unsupported lambda