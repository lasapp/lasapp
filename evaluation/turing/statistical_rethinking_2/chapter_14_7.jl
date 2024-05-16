# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_14.jl

using Turing

@model function m14_7(N, N_households, hidA, hidB, did, giftsAB, giftsBA)
    a ~ Normal()
    ρ_gr ~ LKJ(2, 4)
    σ_gr ~ filldist(Exponential(), 2)
    Σ = (σ_gr .* σ_gr') .* ρ_gr
    gr ~ filldist(MvNormal(Σ), N_households)
    
    # dyad effects (use 2 z values)
    z₁ ~ filldist(Normal(), N)
    z₂ ~ filldist(Normal(), N)
    z = [z₁ z₂]'
    σ_d ~ Exponential()
    ρ_d ~ LKJ(2, 8)
    L_ρ_d = cholesky(Symmetric(ρ_d)).L
    d = (σ_d .* L_ρ_d) * z

    λ_AB = exp.(a .+ gr[1, hidA] .+ gr[2, hidB] .+ d[1, did])
    λ_BA = exp.(a .+ gr[1, hidB] .+ gr[2, hidA] .+ d[2, did])
    for i ∈ eachindex(giftsAB)
        giftsAB[i] ~ Poisson(λ_AB[i])
        giftsBA[i] ~ Poisson(λ_BA[i])
    end
    return d
end

model = m14_7

# MODELGRAPH:
# nodes:
# a, ρ_gr, σ_gr, gr, z₁, z₂, σ_d, ρ_d, giftsAB[i], giftsBA[i]
# edges:
# a -> giftsAB[i]
# a -> giftsBA[i]
# ρ_gr -> gr
# σ_gr -> gr
# gr -> giftsAB[i]
# gr -> giftsBA[i]
# z₁ -> giftsAB[i]
# z₁ -> giftsBA[i]
# z₂ -> giftsAB[i]
# z₂ -> giftsBA[i]
# σ_d -> giftsAB[i]
# σ_d -> giftsBA[i]
# ρ_d -> giftsAB[i]
# ρ_d -> giftsBA[i]
# END_MODELGRAPH

# NOTE: unroll loops to remove spurious edge giftsAB[i] -> giftsAB[i]
# NOTE: unroll loops to remove spurious edge giftsAB[i] -> giftsBA[i]

# NOTE: constraint violation due to member access cholesky().L