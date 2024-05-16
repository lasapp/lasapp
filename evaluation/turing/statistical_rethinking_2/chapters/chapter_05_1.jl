# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_05_1_Spurious_Associations.jl

using Turing

@model function m5_1(A, D)
    σ ~ Exponential(1)
    a ~ Normal(0, 0.2)
    bA ~ Normal(0, 0.5)
    μ = @. a + bA * A
    D ~ MvNormal(μ, σ)
end

@model function m5_2(M, D)
    σ ~ Exponential(1)
    a ~ Normal(0, 0.2)
    bM ~ Normal(0, 0.5)
    μ = @. a + bM * M
    D ~ MvNormal(μ, σ)
end

@model function m5_3(A, M, D)
    σ ~ Exponential(1)
    a ~ Normal(0, 0.2)
    bA ~ Normal(0, 0.5)
    bM ~ Normal(0, 0.5)
    μ = @. a + bA * A + bM * M
    D ~ MvNormal(μ, σ)
end

@model function m5_4(A, M)
    σ ~ Exponential(1)
    a ~ Normal(0, 0.2)
    bAM ~ Normal(0, 0.5)
    μ = @. a + bAM * A
    M ~ MvNormal(μ, σ)
end

@model function m5_3A(A, M, D)
	# A → D ← M
	σ ~ Exponential(1)
	a ~ Normal(0, 0.2)
	bA ~ Normal(0, 0.5)
	bM ~ Normal(0, 0.5)
	μ = @. a + bA * A + bM * M
	D ~ MvNormal(μ, σ)
	# A → M
	σ_M ~ Exponential(1)
	aM ~ Normal(0, 0.2)
	bAM ~ Normal(0, 0.5)
	μ_M = @. aM + bAM * A
	M ~ MvNormal(μ_M, σ_M)
end