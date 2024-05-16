# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_14.jl

using Turing

@model function m14_1(cafe, afternoon, wait)
    a ~ Normal(5, 2)
    b ~ Normal(-1, 0.5)
    σ_cafe ~ filldist(Exponential(), 2)
    Rho ~ LKJ(2, 2)
    # build sigma matrix manually, to avoid numerical errors
#     (σ₁, σ₂) = σ_cafe
#     sc = [[σ₁^2, σ₁*σ₂] [σ₁*σ₂, σ₂^2]]
#     Σ = Rho .* sc
    # the same as above, but shorter and generic
    Σ = (σ_cafe .* σ_cafe') .* Rho
    ab ~ filldist(MvNormal([a,b], Σ), 20)
    a = ab[1,cafe]
    b = ab[2,cafe]
    μ = @. a + b * afternoon
    σ ~ Exponential()
    for i ∈ eachindex(wait)
        wait[i] ~ Normal(μ[i], σ)
    end
end

model = m14_1

# MODELGRAPH:
# nodes:
# a, b, σ_cafe, Rho, ab, σ, wait[i]
# edges:
# a -> ab
# b -> ab
# σ_cafe -> ab
# Rho -> ab
# σ -> wait[i]
# ab -> wait[i]
# ab -> wait[i]
# END_MODELGRAPH

# NOTE: unroll loops to remove spurious edge wait[i] -> wait[i]

# NOTE: constraint violation due to multivariate covariance matrix