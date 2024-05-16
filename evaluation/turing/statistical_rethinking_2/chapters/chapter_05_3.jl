# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_05_3_Categorical_Variables.jl

using Turing

@model function model_m5_8(sex, height)
    σ ~ Uniform(0, 50)
    a ~ MvNormal([178, 178], 20)
    height ~ MvNormal(a[sex], σ)
end

@model function model_m5_9(clade_id, K)
    clade_μ = zeros(clade_counts)
    a ~ MvNormal(clade_μ, 0.5)
    σ ~ Exponential(1)
    K ~ MvNormal(a[clade_id], σ)
end

@model function model_m5_10(clade_id, house, K)
    clade_μ = zeros(clade_counts)
    house_μ = zeros(house_counts)
    a ~ MvNormal(clade_μ, 0.5)
    h ~ MvNormal(house_μ, 0.5)
    σ ~ Exponential(1)
    μ = a[clade_id] .+ h[house]
    K ~ MvNormal(μ, σ)
end
